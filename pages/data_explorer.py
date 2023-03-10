"""
import pandas as pd
import dash
from dash.exceptions import PreventUpdate
from dash import html, Input, Output, State, callback
import dash_bootstrap_components as dbc
from tabulate import tabulate

from data import load_all_sql_files
from pages.utils_worldMap_explorer import WorldMap, DateSlider, TableFilter
from pages.utils_explorer_filter import get_all_references, get_all_frequency_sorted_seqtech, \
    get_all_frequency_sorted_countries_by_filters, get_all_frequency_sorted_countries, \
    get_all_frequency_sorted_mutation, get_frequency_sorted_mutation_by_filters, \
    get_frequency_sorted_seq_techs_by_filters
from pages.html_data_explorer import create_world_map_explorer, html_table_explorer, \
    html_elem_reference_radioitems, html_elem_dropdown_aa_mutations, \
    html_elem_method_radioitems, html_elem_checklist_seq_tech, html_interval, \
    html_elem_dropdown_countries


dash.register_page(__name__, path="/DataExplorer")

# load all data once
location_coordinates = pd.read_csv("data/location_coordinates.csv")
df_dict = load_all_sql_files()
world_map = WorldMap(df_dict["propertyView"], df_dict["variantView"], location_coordinates)
date_slider = DateSlider(df_dict["propertyView"]["COLLECTION_DATE"].tolist())
df_aa_mut = df_dict['variantView'][df_dict['variantView']['element.type'] == 'cds']
table_filter = TableFilter(df_dict["propertyView"], df_dict["variantView"])
all_reference_options = get_all_references(df_dict['variantView'])
all_seq_tech_options = get_all_frequency_sorted_seqtech(df_dict["propertyView"])
all_country_options = get_all_frequency_sorted_countries(df_dict["propertyView"])
all_mutation_options = get_all_frequency_sorted_mutation(world_map.df_all_dates_all_voc, 2)

layout = html.Div(
    [
        html.Div([
            html.Div(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [html_elem_reference_radioitems(all_reference_options)], width=2
                            ),
                            dbc.Col(
                                [html_elem_checklist_seq_tech(all_seq_tech_options)], width=2
                            ),
                            dbc.Col(
                                [html_elem_dropdown_countries(all_country_options)], width=2
                            ),
                            dbc.Col(
                                [html_elem_method_radioitems(),
                                 html_interval()], width=2
                            ),
                        ]
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [html_elem_dropdown_aa_mutations(all_mutation_options)], width=12
                            ),
                        ]
                    ),
                ]
            ),
            html.Div(create_world_map_explorer(date_slider)),
            html.Div(html_table_explorer(table_filter)),
        ], id="div_elem_standard"),
    ]
)


@callback(
    [
        Output("mutation_dropdown", "options"),
        Output("mutation_dropdown", "value"),
        Output("seq_tech_dropdown", "options"),
        Output("seq_tech_dropdown", "value"),
        Output("country_dropdown", "options"),
        Output("country_dropdown", "value"),
        Output('max_nb_txt', 'children'),
        Output('select_x_frequent_mut', 'max')
    ],
    [
        Input("reference_radio", "value"),
        Input("seq_tech_dropdown", "value"),
        Input("country_dropdown", "value"),
        Input("select_x_frequent_mut", "value"),
        Input("select_all_seq_tech", "value"),
        Input("select_all_countries", "value")
    ],
    [
        State("mutation_dropdown", "options"),
        State("mutation_dropdown", "value"),
        State("seq_tech_dropdown", "options"),
        State("country_dropdown", "options"),
        State("select_x_frequent_mut", "value")
    ], prevent_initial_call=False,
)
def frequency_sorted_mutation_by_filters(reference_value, seqtech_value, country_value, select_x_mut, select_all_tech,
                                         select_all_countries, mut_options, mut_value, tech_options, country_options,
                                         freq_nb):
    ""
    filter changing depending on each other
     reference --> seqtech & country & gene & mut
     country --> mut & seqtech
     seqtech -->  mut & country
     gene --> mut & seqtech & country
     mut --> no callback
    ""
    print(dash.ctx.triggered_id)
    df_mut_ref_select = df_aa_mut[(df_aa_mut['reference.id'] == reference_value)]
    if dash.ctx.triggered_id == "select_all_seq_tech":
        if len(select_all_tech) == 1:
            seqtech_value = [i['value'] for i in all_seq_tech_options if not i['disabled']]
        elif len(select_all_tech) == 0:
            seqtech_value = []

    # TODO now return top x mut without checking for mutations with same number
    if dash.ctx.triggered_id == "select_x_frequent_mut":
        mut_value = [i['value'] for i in mut_options[0: select_x_mut]]

    if dash.ctx.triggered_id == "select_all_countries":
        if len(select_all_countries) == 1:
            country_value = [i['value'] for i in country_options if not i['disabled']]
        elif len(select_all_countries) == 0:
            country_value = []

    # mutation_option
    if dash.ctx.triggered_id in ["reference_radio", "seq_tech_dropdown", "country_dropdown",
                                 "select_all_seq_tech", "select_all_countries"]:
        df_seq_tech = df_dict['propertyView'][(df_dict['propertyView']["SEQ_TECH"].isin(seqtech_value)) &
                                              (df_dict['propertyView']["COUNTRY"].isin(country_value))]
        mut_options = get_frequency_sorted_mutation_by_filters(df_mut_ref_select, df_seq_tech)
        if dash.ctx.triggered_id == "reference_radio" or len(mut_value) == 0:
            mut_value = [m['value'] for m in mut_options][0:freq_nb]
        else:
            mut_value = [mut for mut in mut_value if mut in [m['value'] for m in mut_options]]

    # seq tech disable options
    if dash.ctx.triggered_id in ["reference_radio"]:
        tech_options = get_frequency_sorted_seq_techs_by_filters(df_mut_ref_select,  df_dict['propertyView'],
                                                                 tech_options)
        seqtech_value = [tech for tech in seqtech_value if tech in
                         [t['value'] for t in tech_options if not t['disabled']]]

    # countries disable options
    if dash.ctx.triggered_id in ["reference_radio", "seq_tech_dropdown", "select_all_seq_tech"]:
        sample_id_set = set(df_mut_ref_select['sample.id'])
        df_prop = df_dict['propertyView'][(df_dict['propertyView']["SEQ_TECH"].isin(seqtech_value)) &
                                          (df_dict['propertyView']["sample.id"].isin(sample_id_set))]
        country_options = get_all_frequency_sorted_countries_by_filters(df_prop, country_options)
        country_value = [o['value'] for o in country_options if not o['disabled']]

    text = f"Select x most frequent sequences. Maximum number of non-unique mutations: {len(mut_options)}",

    return mut_options, mut_value, tech_options, seqtech_value, country_options, country_value, text, len(mut_options)


# update map by change of filters or moving slider
@callback(
    Output("world_map_explorer", "figure"),
    [
        Input("mutation_dropdown", "value"),
        Input("reference_radio", "value"),
        Input("method_radio", "value"),
        Input("seq_tech_dropdown", "value"),
        Input("selected_interval", "value"),
        Input('date_slider', 'value'),
        Input("country_dropdown", "value")
    ],
    [
        State('world_map_explorer', 'relayoutData'),
    ], prevent_initial_call=True,
)
def update_world_map_explorer(mutation_list, reference_id, method, seqtech_list, interval, dates, countries, layout):
    print("trigger new map")
    date_list = date_slider.get_all_dates_in_interval(dates, interval)
    fig = world_map.get_world_map(mutation_list, reference_id, seqtech_list, method, date_list, countries)
    # layout: {'geo.projection.rotation.lon': -99.26450411962647, 'geo.center.lon': -99.26450411962647,
    # 'geo.center.lat': 39.65065298875763, 'geo.projection.scale': 2.6026837108838667}
    # TODO sometimes not working
    if layout:
        fig.update_layout(layout)
    print("fig returned")
    return fig


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
    ""
    slider moved by user drag, changed location of slider with drag_value
    OR
    slider moved by auto_stepper (activated by play-button)
    ""
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
    ""
    stop and start auto-stepper (disabled value), returns play or stop icon for button
    interval: increment the counter n_intervals every interval milliseconds.
    disabled (boolean; optional): If True, the counter will no longer update.
    n_intervals (number; default 0): Number of times the interval has passed.
    max_intervals (number; default -1): Number of times the interval will be fired. If -1, then the interval has no limit
    (the default) and if 0 then the interval stops running.
    ""
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
    ], prevent_initial_call=True,
)
def update_lower_plot(click_data_map, mutations, reference_id, seqtech_list, dates, interval, clickDataBoxPlot):
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
        Input('date_slider', 'value'),
        Input("country_dropdown", "value")
    ], prevent_initial_call=True,
)
def update_table_filter(mutation_list, reference_id, seqtech_list, interval, dates, countries):
    date_list = date_slider.get_all_dates_in_interval(dates, interval)
    table_df = table_filter.get_filtered_table(mutation_list, seqtech_list, reference_id, date_list)
    return table_df.to_dict('records'), [{"name": i, "id": i} for i in table_df.columns]

"""
