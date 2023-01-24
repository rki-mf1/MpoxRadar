"""


import pandas as pd
import dash
from dash import callback
from dash.exceptions import PreventUpdate
from dash import html
from dash import Input
from dash import Output
from dash import State
import dash_bootstrap_components as dbc

from pages.checklist_filter import get_html_elem_reference_radioitems, get_html_elem_checklist_aa_mutations, \
    get_html_elem_method_radioitems, get_html_elem_checklist_seq_tech, get_html_interval, get_all_references, \
    get_all_frequency_sorted_seqtech
from pages.checklist_filter import get_frequency_sorted_mutation_by_filters, get_frequency_sorted_seq_techs_by_filters
from data import load_all_sql_files
from pages.html_data_explorer import create_worldMap_explorer, create_table_explorer
from pages.utils_worldMap_filter import WorldMap, DateSlider, TableFilter

# dash.register_page(__name__, path="/DataExplorer")

# load all data once
location_coordinates = pd.read_csv("data/location_coordinates.csv")
df_dict = load_all_sql_files()
world_map = WorldMap(df_dict["propertyView"], df_dict["variantView"], location_coordinates)
date_slider = DateSlider(df_dict["propertyView"]["COLLECTION_DATE"].tolist())
df_mut = df_dict['variantView'][df_dict['variantView']['element.type'] == 'cds']
table_filter = TableFilter(df_dict["propertyView"], df_dict["variantView"])
reference_options = get_all_references(df_dict['variantView'])
seq_tech_options = get_all_frequency_sorted_seqtech(df_dict["propertyView"])

layout = html.Div(
    [
        html.Div(id="alertmsg"),
        html.Div([
            html.Div(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [get_html_elem_reference_radioitems(reference_options)], width=2
                            ),
                            dbc.Col(
                                [get_html_elem_checklist_aa_mutations(df_dict["variantView"], reference_id=2)], width=2
                            ),
                            dbc.Col(
                                [get_html_elem_checklist_seq_tech(seq_tech_options)], width=2
                            ),

                            dbc.Col(
                                [get_html_elem_method_radioitems(),
                                 get_html_interval()], width=2
                            ),
                        ]
                    ),
                ]
            ),
            html.Div(create_worldMap_explorer(date_slider)),
            html.Div(create_table_explorer(table_filter)),
        ], id="div_elem_standard"),
    ]
)


# @callback(
#     Output("seq_tech_dropdown", "value"),
#     [Input("seqtech_all-or-none", "value")],
#     [State("seq_tech_dropdown", "options")],
# )
# def seqtech_select_all_none(all_selected, options):
#     all_or_none = [option for option in options if all_selected]
#     return all_or_none

# refill filters depending on selected filter
@callback(
    [
        Output("mutation_dropdown", "options"),
        Output("mutation_dropdown", "value"),
        Output("seq_tech_dropdown", "options"),
        Output("seq_tech_dropdown", "value"),
        # Output("reference_radio", "options"),
        # Output("reference_radio", "value"),
    ],
    [
        Input("reference_radio", "value"),
        Input("seq_tech_dropdown", "value"),
        Input("mutation_dropdown", "value"),
        Input("select_all_mut", "value"),
        Input("select_all_seq_tech", "value")
    ],
    [
        State("mutation_dropdown", "options"),
        State("seq_tech_dropdown", "options"),
   #     State("reference_radio", "options")
    ], prevent_initial_call=False,
)
def frequency_sorted_mutation_by_filters(reference_value, seqtech_value, mut_value, select_all_mut, select_all_tech,
                                         mut_options, tech_options):

    # different filters depending on each other (exception reference genome, do not change)


    if dash.ctx.triggered_id == "select_all_seq_tech":
        if len(select_all_tech) == 1:
            seqtech_value = [i['value'] for i in seq_tech_options]
        elif len(select_all_tech) == 0:
            seqtech_value = []

    if dash.ctx.triggered_id == "select_all_mut":
        if len(select_all_mut) == 1:
            mut_value = [i['value'] for i in mut_options]
        elif len(select_all_mut) == 0:
            mut_value = []

    # mutation_option
    if dash.ctx.triggered_id in ["reference_radio", "seq_tech_dropdown", "select_all_seq_tech"]:
        df_seq_tech = df_dict['propertyView'][df_dict['propertyView']["SEQ_TECH"].isin(seqtech_value)]
        df_mut_ref_select = df_mut[(df_mut['reference.id'] == reference_value)]
        mut_options = get_frequency_sorted_mutation_by_filters(df_mut_ref_select, df_seq_tech)
        print('mut_option: ', len(mut_options))
        if len(mut_options) > 20:
            mut_value = [mut_dict['value'] for mut_dict in mut_options[0:20] if mut_dict['value'] in mut_value]
        else:
            mut_value = [mut_dict['value'] for mut_dict in mut_options if mut_dict['value'] in mut_value]
        print('mut_value: ', len(mut_value))
    # seq tech
    if dash.ctx.triggered_id in ["reference_radio", "mutation_dropdown", "select_all_mut"]:
        df_mut_ref_mut_select = df_mut[
            (df_mut["variant.label"].isin(mut_value) &
             (df_mut['reference.id'] == reference_value))
        ]
        tech_options = get_frequency_sorted_seq_techs_by_filters(df_mut_ref_mut_select, df_dict['propertyView'])
        seqtech_value = [seq_tech_dict['value'] for seq_tech_dict in tech_options if seq_tech_dict['value'] in
                         seqtech_value]

    # # reference
    # if dash.ctx.triggered_id in ["seq_tech_dropdown", "mutation_dropdown", "select_all_mut"]:
    #     df_seq_tech = df_dict['propertyView'][df_dict['propertyView']["SEQ_TECH"].isin(seqtech_value)]
    #     df_mut_mut_select = df_mut[df_mut["variant.label"].isin(mut_value)]
    #     ref_options = get_reference_options_by_filters(df_mut_mut_select, df_seq_tech, reference_options)
    #     reference_options_values = [ref_dict['value'] for ref_dict in ref_options]
    #     try:
    #         reference_value = reference_value if reference_value in reference_options_values else \
    #             reference_options_values[0]
    #     except IndexError:
    #         reference_value = 2

    return mut_options, mut_value, tech_options, seqtech_value


# update map by change of filters or moving slider
@callback(
    Output("world_map_explorer", "figure"),
    [
        Input("mutation_dropdown", "value"),
        Input("reference_radio", "value"),
        Input("method_radio", "value"),
        Input("seq_tech_dropdown", "value"),
        Input("selected_interval", "value"),
        Input('date_slider', 'value')
    ],
    [
        State('world_map_explorer', 'figure'),
    ], prevent_initial_call=True,
)
def update_world_map_explorer(mutation_list, reference_id, method, seqtech_list, interval, dates, map_json):
    print("trigger new map")
    date_list = date_slider.get_all_dates_in_interval(dates, interval)
    if map_json:
        if "zoom" in map_json['layout']['mapbox']:
            zoom = map_json['layout']['mapbox']['zoom']
        else:
            zoom = None
        center = map_json['layout']['mapbox']['center']
    else:
        zoom, center = None, None
    # map mutations, reference_id, seq_tech_list, method, dates, mode='absolute frequencies', nth=0
    fig = world_map.get_world_map(mutation_list, reference_id, seqtech_list, method, date_list, zoom, center)
    print("fig returned")
    return fig


# slider interval updated during drag (drag_value)
# slider interval updated by play-button and Interval
@callback(
    Output('date_slider', 'value'),
    [
        Input('date_slider', 'drag_value'),
        Input('selected_interval', 'value'),
        Input('auto_stepper', "n_intervals"),
    ],
    [
        State('date_slider', 'value'),
    ], prevent_initial_call=True,
)
def update_slider_interval(drag_value, interval, n_intervals, slider_value):

    # slider moved by user drag, changed location of slider with drag_value
    # OR
    # slider moved by auto_stepper (activated by play-button)

    if interval is None:
        interval = 0
    # if interval changed or slider moved:
    if dash.ctx.triggered_id in ["selected_interval", "date_slider"]:
        if not drag_value:
            return slider_value
        if len(drag_value) == 2:
            second_date = drag_value[-1]
            if DateSlider.get_date_x_days_before(DateSlider.unix_to_date(second_date), interval) > date_slider.min_date:
                new_first_date = DateSlider.unix_time_millis(DateSlider.get_date_x_days_before
                                                             (DateSlider.unix_to_date(second_date), interval))
            else:
                new_first_date = DateSlider.unix_time_millis(date_slider.min_date)
            return [new_first_date, second_date]
        else:
            return slider_value
    # if play button starts auto_stepper
    if dash.ctx.triggered_id == 'auto_stepper':
        if n_intervals == 0:
            # raise PreventUpdate
            return slider_value
        if interval is None:
            interval = 7
        if n_intervals + interval >= len(date_slider.date_list):
            first_date = DateSlider.unix_time_millis(date_slider.date_list[-interval])
            second_date = DateSlider.unix_time_millis(date_slider.date_list[-1])
        else:
            first_date = DateSlider.unix_time_millis(date_slider.date_list[n_intervals - 1])
            second_date = DateSlider.unix_time_millis(
                date_slider.date_list[n_intervals + interval - 1])  # first_date + interval*86400
        return [first_date, second_date]


@callback(
    [
        Output('auto_stepper', 'max_intervals'),
        Output('auto_stepper', 'disabled'),
        Output('play_button', 'className'),
    ],
    [
        Input('play_button', 'n_clicks'),
        Input('auto_stepper', 'n_intervals'),
    ],
    [
        State('selected_interval', 'value'),
        State('play_button', 'className')
    ], prevent_initial_call=True,
)
def stepper_control(n_clicks, n_intervals, interval, button_icon):

    # stop and start auto-stepper (disabled value), returns play or stop icon for button
    # interval: increment the counter n_intervals every interval milliseconds.
    # disabled (boolean; optional): If True, the counter will no longer update.
    # n_intervals (number; default 0): Number of times the interval has passed.
    # max_intervals (number; default -1): Number of times the interval will be fired. If -1, then the interval has no limit
    # (the default) and if 0 then the interval stops running.

    if interval is None:
        interval = 0
    steps = len(date_slider.date_list) - interval
    # stop stepper
    if dash.ctx.triggered_id == 'play_button':
        # start stepper
        if button_icon == 'fa-solid fa-circle-play fa-lg':
            return steps, False, "fa-solid fa-circle-stop fa-lg"
        # pause stepper
        elif button_icon == "fa-solid fa-circle-stop fa-lg":
            return steps, True, "fa-solid fa-circle-play fa-lg"
    else:
        if n_intervals == steps:
            return 0, True, "fa-solid fa-circle-play fa-lg"
        else:
            raise PreventUpdate


# update plots
@callback(
    [
        Output('results_per_location', 'figure'),
        Output('chosen_location', 'children'),
        Output('header_upper_plot', 'children')
    ],
    [
        Input('world_map_explorer', 'clickData'),
        Input('mutation_dropdown', 'value'),
        Input('method_radio', 'value'),
        Input('reference_radio', 'value'),
        Input("seq_tech_dropdown", "value"),
        Input('date_slider', 'value'),
        Input('selected_interval', 'value'),
        #   Input('yaxis_type', 'value')
    ], prevent_initial_call=True,
)
def update_upper_plot(click_data, mutations, method, reference_id, seqtech_list, dates, interval):
    # get click data {'points': [{'curveNumber': 19, 'pointNumber': 3, 'pointIndex': 3, 'lon': 10.451526,
    # 'lat': 51.165691, 'hovertext': 'Germany', 'marker.size': 30,
    # 'bbox': {'x0': 877.5110333644036, 'x1': 919.9374402355966, 'y0': 243.83076680322816, 'y1': 286.257173674421},
    # 'customdata': ['V125G', 167, 'Germany', 51.165691, 10.451526, 30]}]}
    # print(f"start plot: {datetime.now()}")
    try:
        location_name = click_data['points'][0]['hovertext']
    except TypeError:
        location_name = "Germany"
    # date from slider
    date_list = date_slider.get_all_dates_in_interval(dates, interval)
    # title text
    title_text = location_name
    # 1. plot
    if method == 'Increase':
        fig = world_map.get_slope_bar_plot(date_list, mutations, reference_id, seqtech_list, location_name)
        plot_header = "Slope mutations"
    elif method == 'Frequency':
        fig = world_map.get_frequency_bar_chart(mutations, reference_id, seqtech_list, date_list, location_name)
        plot_header = "Number Sequences"
    return fig, title_text, plot_header


@callback(
    Output('mutation_development', 'figure'),
    [
        Input('world_map_explorer', 'clickData'),
        Input('mutation_dropdown', 'value'),
        Input('reference_radio', 'value'),
        Input("seq_tech_dropdown", "value"),
        Input('date_slider', 'value'),
        Input('selected_interval', 'value'),
        Input("results_per_location", 'clickData'),
        #   Input('yaxis_type', 'value'),
    ], prevent_initial_call=True,
)
def update_lower_plot(click_data_map, mutations, reference_id, seqtech_list, dates, interval, clickDataBoxPlot):
    # get click data {'points': [{'curveNumber': 19, 'pointNumber': 3, 'pointIndex': 3, 'lon': 10.451526,
    # 'lat': 51.165691, 'hovertext': 'Germany', 'marker.size': 30,
    # 'bbox': {'x0': 877.5110333644036, 'x1': 919.9374402355966, 'y0': 243.83076680322816, 'y1': 286.257173674421},
    # 'customdata': ['V125G', 167, 'Germany', 51.165691, 10.451526, 30]}]}
    # click_data['points'][0]['customdata'] = ['V125G', 167, 'Germany', 51.165691, 10.451526, 30]
    # = [mut, nb_seq, location_name, location_ID, lat, lon, size
    # print(f"start plot: {datetime.now()}")
    if dash.ctx.triggered_id == "results_per_location":
        mutations = [clickDataBoxPlot['points'][0]['label']]
    try:
        location_name = click_data_map['points'][0]['hovertext']
    except TypeError:
        location_name = "Germany"
    date_list = date_slider.get_all_dates_in_interval(dates, interval)
    fig_develop = world_map.get_frequency_development_scatter_plot(mutations, reference_id, seqtech_list, date_list,
                                                                   location_name)
    return fig_develop


# fill table
@callback(
    [
        Output(component_id="table_explorer", component_property="data"),
        Output(component_id="table_explorer", component_property="columns")
    ],
    [
        Input("mutation_dropdown", "value"),
        Input("reference_radio", "value"),
        Input("seq_tech_dropdown", "value"),
        Input("selected_interval", "value"),
        Input('date_slider', 'value')
    ], prevent_initial_call=True,
)
def update_table_filter(mutation_list, reference_id, seqtech_list, interval, dates):
    date_list = date_slider.get_all_dates_in_interval(dates, interval)
    table_df = table_filter.get_filtered_table(mutation_list, seqtech_list, reference_id, date_list)
    return table_df.to_dict('records'), [{"name": i, "id": i} for i in table_df.columns]
"""
