
import dash
from dash.exceptions import PreventUpdate
from dash import Input, Output, State, callback

from pages.utils_worldMap_explorer import DateSlider
from pages.utils_explorer_filter import get_all_frequency_sorted_countries_by_filters, \
    get_frequency_sorted_mutation_by_filters, \
    get_frequency_sorted_seq_techs_by_filters,\
    get_all_genes_per_reference


# This is the EXPLORE TOOL PART
def get_explore_callbacks(df_dict, world_map, date_slider, variantView_cds, table_filter, all_seq_tech_options):

    @callback(
        [
            Output("mutation_dropdown_0", "options"),
            Output("mutation_dropdown_0", "value"),
            Output('max_nb_txt_0', 'children'),
            Output('select_x_frequent_mut_0', 'max'),
            Output("select_x_frequent_mut_0", "value"),
        ],
        [
            Input("reference_radio_0", "value"),
            Input("gene_dropdown_0", "value"),
            Input("seq_tech_dropdown_0", "value"),
            Input("country_dropdown_0", "value"),
            Input("select_x_frequent_mut_0", "value"),
        ],
        [
            State("mutation_dropdown_0", "options"),
        ], prevent_initial_call=False,
        )
    def actualize_mutation_filter(reference_value, gene_value, seqtech_value, country_value, select_x_mut,
                                  mut_options):
        """
        filter changing depending on each other
         reference --> seqtech & country & gene & mut
         country --> mut
         seqtech -->  mut & country
         gene --> mut
         mut --> no callback
        """
        # TODO now return top x mut without checking for mutations with same number
        if dash.ctx.triggered_id == "select_x_frequent_mut_0":
            mut_value = [i['value'] for i in mut_options[0: select_x_mut]]

        else:
            variantView_cds_ref = variantView_cds[(variantView_cds['reference.id'] == reference_value)]
            propertyView_seq_country = df_dict['propertyView'][
                (df_dict['propertyView']["SEQ_TECH"].isin(seqtech_value)) &
                (df_dict['propertyView']["COUNTRY"].isin(country_value))]
            variantView_cds_ref_gene = variantView_cds_ref[variantView_cds_ref["element.symbol"].isin(gene_value)]
            mut_options = get_frequency_sorted_mutation_by_filters(variantView_cds_ref_gene, propertyView_seq_country)
            if select_x_mut > len(mut_options):
                select_x_mut = len(mut_options)
            mut_value = [i['value'] for i in mut_options][0:select_x_mut]

        text = f"Select x most frequent sequences. Maximum number of mutations (including unique mutations) with chosen " \
               f"filter options: {len(mut_options)}"
        return mut_options, mut_value, text, len(mut_options), select_x_mut

    @callback(
        [
            Output("gene_dropdown_0", "options"),
            Output("gene_dropdown_0", "value"),
        ],
        [
            Input("reference_radio_0", "value"),
            Input("gene_dropdown_0", "value"),
            Input("select_all_genes_0", "value"),
        ],
        [
            State("gene_dropdown_0", "options"),
        ], prevent_initial_call=False,
        )
    def actualize_gene_filters(reference_value, gene_value, select_all_genes, gene_options):
        """
         gene --> mut
        """
        if dash.ctx.triggered_id == "select_all_genes_0":
            if len(select_all_genes) == 1:
                gene_value = [i['value'] for i in get_all_genes_per_reference(df_dict["referenceView"], reference_value)]
            elif len(select_all_genes) == 0:
                gene_value = []
        if dash.ctx.triggered_id in ["reference_radio_0"]:
            gene_options = get_all_genes_per_reference(df_dict["referenceView"], reference_value)
            gene_value = [i['value'] for i in gene_options]

        return gene_options, gene_value


    @callback(
        [
            Output("seq_tech_dropdown_0", "options"),
            Output("seq_tech_dropdown_0", "value"),
            Output("country_dropdown_0", "options"),
            Output("country_dropdown_0", 'value'),
        ],
        [
            Input("reference_radio_0", "value"),
            Input("seq_tech_dropdown_0", "value"),
            Input("country_dropdown_0", "value"),
            Input("select_all_seq_tech_0", "value"),
            Input("select_all_countries_0", "value")
        ],
        [
            State("seq_tech_dropdown_0", "options"),
            State("country_dropdown_0", "options"),
        ], prevent_initial_call=False,
        )
    def actualize_seqtech_and_country_filters(reference_value, seqtech_value, country_value, select_all_tech,
                                              select_all_countries, tech_options, country_options):
        """
         seqtech changes mut & country filter; is changed by ref
         country changes mut filter; is changed by ref and country (keep prior country selection)
        """
        print(dash.ctx.triggered_id )
        if dash.ctx.triggered_id == "select_all_seq_tech_0":
            if len(select_all_tech) == 1:
                seqtech_value = [i['value'] for i in all_seq_tech_options if not i['disabled']]
            elif len(select_all_tech) == 0:
                seqtech_value = []
        elif dash.ctx.triggered_id == "select_all_countries_0":
            if len(select_all_countries) == 1:
                country_value = [i['value'] for i in country_options if not i['disabled']]
            elif len(select_all_countries) == 0:
                country_value = []
        # countries disable options, seq tech disable options
        else:
            variantView_cds_ref = variantView_cds[(variantView_cds['reference.id'] == reference_value)]
            tech_options = get_frequency_sorted_seq_techs_by_filters(variantView_cds_ref, df_dict['propertyView'],
                                                                     tech_options)
            seqtech_value = [tech for tech in seqtech_value if tech in [t['value'] for t in tech_options
                                                                        if not t['disabled']]]
            sample_id_set = set(variantView_cds_ref['sample.id'])
            df_prop = df_dict['propertyView'][(df_dict['propertyView']["SEQ_TECH"].isin(seqtech_value)) &
                                              (df_dict['propertyView']["sample.id"].isin(sample_id_set))]
            country_options = get_all_frequency_sorted_countries_by_filters(df_prop, country_options)
            country_value = [c['value'] for c in country_options if not c['disabled'] and c['value'] in country_value]
        print(country_value)

        return tech_options, seqtech_value, country_options, country_value


    # update map by change of filters or moving slider
    @callback(
        Output("world_map_explorer", "figure"),
        [
            Input("mutation_dropdown_0", "value"),
            Input("reference_radio_0", "value"),
            Input("method_radio", "value"),
            Input("seq_tech_dropdown_0", "value"),
            Input("selected_interval", "value"),
            Input('date_slider', 'value'),
            Input("country_dropdown_0", "value")
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
        """
        slider moved by user drag, changed location of slider with drag_value
        OR
        slider moved by auto_stepper (activated by play-button)
        """
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
        """
        stop and start auto-stepper (disabled value), returns play or stop icon for button
        interval: increment the counter n_intervals every interval milliseconds.
        disabled (boolean; optional): If True, the counter will no longer update.
        n_intervals (number; default 0): Number of times the interval has passed.
        max_intervals (number; default -1): Number of times the interval will be fired. If -1, then the interval has no limit
        (the default) and if 0 then the interval stops running.
        """
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
            Input('mutation_dropdown_0', 'value'),
            Input('method_radio', 'value'),
            Input('reference_radio_0', 'value'),
            Input("seq_tech_dropdown_0", "value"),
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
            Input('mutation_dropdown_0', 'value'),
            Input('reference_radio_0', 'value'),
            Input("seq_tech_dropdown_0", "value"),
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
            Input("mutation_dropdown_0", "value"),
            Input("reference_radio_0", "value"),
            Input("gene_dropdown_0", "value"),
            Input("seq_tech_dropdown_0", "value"),
            Input("selected_interval", "value"),
            Input('date_slider', 'value'),
            Input("country_dropdown_0", "value")
        ], prevent_initial_call=True,
        )
    def update_table_filter(mutation_list, reference_id, gene_list, seqtech_list, interval, dates, countries):
        date_list = date_slider.get_all_dates_in_interval(dates, interval)
        table_df = table_filter.get_filtered_table(mutation_list, seqtech_list, reference_id, date_list, gene_list,
                                                   countries)
        return table_df.to_dict('records'), [{"name": i, "id": i} for i in table_df.columns]
