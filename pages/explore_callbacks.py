from dash import callback
from dash import ctx
from dash import Input
from dash import Output
from dash import State

from pages.utils_filters import actualize_filters
from pages.utils_filters import get_frequency_sorted_cds_mutation_by_filters
from pages.utils_tables import TableFilter
from pages.utils_worldMap_explorer import DateSlider
from pages.utils_worldMap_explorer import DetailPlots
from pages.utils_worldMap_explorer import WorldMap


def get_explore_callbacks(  # noqa: C901
    df_dict, date_slider, color_dict, location_coordinates
):
    """
    function contains all callbacks used in explore tool page (in tool.py file)
    """

    @callback(
        [
            Output("mutation_dropdown_0", "options"),
            Output("mutation_dropdown_0", "value"),
            Output("max_nb_txt_0", "children"),
            Output("select_x_frequent_mut_0", "max"),
            Output("select_x_frequent_mut_0", "value"),
            Output("select_min_nb_frequent_mut_0", "value"),
            Output("min_nb_freq_0", "children"),
        ],
        [
            Input("reference_radio_0", "value"),
            Input("gene_dropdown_0", "value"),
            Input("seq_tech_dropdown_0", "value"),
            Input("country_dropdown_0", "value"),
            Input("select_x_frequent_mut_0", "value"),
            Input("complete_partial_radio_explore", "value"),
            Input("select_min_nb_frequent_mut_0", "value"),
        ],
        [
            State("mutation_dropdown_0", "options"),
            State("min_nb_freq_0", "children"),
        ],
        prevent_initial_call=False,
    )
    def actualize_mutation_filter(
        reference_value,
        gene_value,
        seqtech_value,
        country_value,
        select_x_mut,
        complete_partial_radio,
        min_nb_freq,
        mut_options,
        text_freq,
    ):
        # TODO now return top x mut without checking for mutations with same number
        if ctx.triggered_id == "select_x_frequent_mut_0":
            mut_value = [i["value"] for i in mut_options[0:select_x_mut]]
            max_select = len(mut_options)

        else:
            (
                mut_options,
                max_nb_freq,
                min_nb_freq,
            ) = get_frequency_sorted_cds_mutation_by_filters(
                df_dict,
                seqtech_value,
                country_value,
                gene_value,
                complete_partial_radio,
                reference_value,
                color_dict,
                min_nb_freq,
            )
            max_select = len(mut_options)
            if len(mut_options) < 20:
                select_x_mut = len(mut_options)
            else:
                select_x_mut = 20
            mut_value = [i["value"] for i in mut_options][0:select_x_mut]
            text_freq = (
                f"Select minimum variant frequency. Highest frequency: {max_nb_freq}"
            )
        text_nb_mut = f"Select n-th most frequent variants. Number variants matching filters: \
            {len(mut_options)}"

        return (
            mut_options,
            mut_value,
            text_nb_mut,
            max_select,
            select_x_mut,
            min_nb_freq,
            text_freq,
        )

    @callback(
        [
            Output("gene_dropdown_0", "options"),
            Output("gene_dropdown_0", "value"),
            Output("country_dropdown_0", "options"),
            Output("country_dropdown_0", "value"),
            Output("seq_tech_dropdown_0", "options"),
            Output("seq_tech_dropdown_0", "value"),
        ],
        [
            Input("reference_radio_0", "value"),
            Input("select_all_seq_tech_0", "value"),
            Input("select_all_genes_0", "value"),
            Input("select_all_countries_0", "value"),
            Input("complete_partial_radio_explore", "value"),
            Input("seq_tech_dropdown_0", "value"),
            Input("gene_dropdown_0", "value"),
        ],
        [
            State("gene_dropdown_0", "options"),
            State("country_dropdown_0", "options"),
            State("seq_tech_dropdown_0", "options"),
            State("country_dropdown_0", "value"),
        ],
        prevent_initial_call=True,
    )
    def actualize_filters_explorer(
        reference_value,
        select_all_seq_techs,
        select_all_genes,
        select_all_countries,
        complete_partial_radio,
        seq_tech_value,
        gene_value,
        gene_options,
        country_options,
        seq_tech_options,
        country_value,
    ):
        """
        seqtech changes mut & country filter; is changed by ref
        country changes mut filter; is changed by ref and seqtech (keep prior country selection)
        """
        return actualize_filters(
            df_dict,
            color_dict,
            ctx.triggered_id,
            "cds",
            reference_value,
            select_all_seq_techs,
            select_all_genes,
            select_all_countries,
            complete_partial_radio,
            gene_options,
            country_options,
            seq_tech_options,
            gene_value,
            country_value,
            seq_tech_value,
            str(date_slider.min_date),
        )

    # update map by change of filters or moving slider
    @callback(
        Output("world_map_explorer", "figure"),
        [
            Input("mutation_dropdown_0", "value"),
            Input("reference_radio_0", "value"),
            Input("method_radio", "value"),
            Input("seq_tech_dropdown_0", "value"),
            Input("selected_interval", "value"),
            Input("date_slider", "value"),
            Input("country_dropdown_0", "value"),
            Input("complete_partial_radio_explore", "value"),
        ],
        [
            State("world_map_explorer", "relayoutData"),
        ],
        prevent_initial_call=True,
    )
    # @cache.memoize()
    def update_world_map_explorer(
        mutation_list,
        reference_id,
        method,
        seqtech_list,
        interval,
        dates,
        countries,
        complete_partial_radio,
        layout,
    ):
        world_map_instance = WorldMap(
            df_dict,
            date_slider,
            reference_id,
            complete_partial_radio,
            countries,
            seqtech_list,
            mutation_list,
            dates,
            interval,
            color_dict,
            location_coordinates,
        )
        fig = world_map_instance.get_world_map(method)
        # layout: {'geo.projection.rotation.lon': -99.26450411962647,
        #          'geo.center.lon': -99.26450411962647,
        #           'geo.center.lat': 39.65065298875763,
        #           'geo.projection.scale': 2.6026837108838667
        # }
        # TODO sometimes not working
        if layout:
            fig.update_layout(layout)
        return fig

    @callback(
        Output("date_slider", "value"),
        [
            Input("date_slider", "drag_value"),
            Input("selected_interval", "value"),
            #   Input("auto_stepper", "n_intervals"),
        ],
        [
            State("date_slider", "value"),
        ],
        prevent_initial_call=True,
    )
    def update_slider_interval(
        drag_value,
        interval,
        # n_intervals,
        slider_value,
    ):
        """
        slider moved by user drag, changed location of slider with drag_value
        OR
        slider moved by auto_stepper (activated by play-button)
        """
        if interval is None:
            interval = 0
        # if interval changed or slider moved:
        if ctx.triggered_id in ["selected_interval", "date_slider"]:
            if not drag_value:
                return slider_value
            if len(drag_value) == 2:
                second_date = drag_value[-1]
                if (
                    DateSlider.get_date_x_days_before(
                        DateSlider.unix_to_date(second_date), interval
                    )
                    > date_slider.min_date
                ):
                    new_first_date = DateSlider.unix_time_millis(
                        DateSlider.get_date_x_days_before(
                            DateSlider.unix_to_date(second_date), interval
                        )
                    )
                else:
                    new_first_date = DateSlider.unix_time_millis(date_slider.min_date)
                return [new_first_date, second_date]
            else:
                return slider_value
        # if play button starts auto_stepper
        # if ctx.triggered_id == "auto_stepper":
        #     if n_intervals == 0:
        #         # raise PreventUpdate
        #         return slider_value
        #     if interval is None:
        #         interval = 7
        #     if n_intervals + interval >= len(date_slider.date_list):
        #         first_date = DateSlider.unix_time_millis(
        #             date_slider.date_list[-interval]
        #         )
        #         second_date = DateSlider.unix_time_millis(date_slider.date_list[-1])
        #     else:
        #         first_date = DateSlider.unix_time_millis(
        #             date_slider.date_list[n_intervals - 1]
        #         )
        #         second_date = DateSlider.unix_time_millis(
        #             date_slider.date_list[n_intervals + interval - 1]
        #         )  # first_date + interval*86400
        #     return [first_date, second_date]

    #
    # @callback(
    #     [
    #         Output("auto_stepper", "max_intervals"),
    #         Output("auto_stepper", "disabled"),
    #         Output("play_button", "className"),
    #     ],
    #     [
    #         Input("play_button", "n_clicks"),
    #         Input("auto_stepper", "n_intervals"),
    #     ],
    #     [State("selected_interval", "value"), State("play_button", "className")],
    #     prevent_initial_call=True,
    # )
    # def stepper_control(n_clicks, n_intervals, interval, button_icon):
    #     """
    #     stop and start auto-stepper (disabled value), returns play or stop icon for button
    #     interval: increment the counter n_intervals every interval milliseconds.
    #     disabled (boolean; optional): If True, the counter will no longer update.
    #     n_intervals (number; default 0): Number of times the interval has passed.
    #     max_intervals (number; default -1): Number of times the interval will be fired.
    #      If -1, then the interval has no limit
    #     (the default) and if 0 then the interval stops running.
    #     """
    #     if interval is None:
    #         interval = 0
    #     steps = len(date_slider.date_list) - interval
    #     # stop stepper
    #     if ctx.triggered_id == "play_button":
    #         # start stepper
    #         if button_icon == "fa-solid fa-circle-play fa-lg":
    #             return steps, False, "fa-solid fa-circle-stop fa-lg"
    #         # pause stepper
    #         elif button_icon == "fa-solid fa-circle-stop fa-lg":
    #             return steps, True, "fa-solid fa-circle-play fa-lg"
    #     else:
    #         if n_intervals == steps:
    #             return 0, True, "fa-solid fa-circle-play fa-lg"
    #         else:
    #             raise PreventUpdate

    # update plots

    @callback(
        [
            Output("results_per_location", "figure"),
            Output("chosen_location", "children"),
            Output("header_upper_plot", "children"),
            Output("sequence_information", "children"),
        ],
        [
            Input("world_map_explorer", "clickData"),
            Input("mutation_dropdown_0", "value"),
            Input("method_radio", "value"),
            Input("reference_radio_0", "value"),
            Input("seq_tech_dropdown_0", "value"),
            Input("date_slider", "value"),
            Input("selected_interval", "value"),
            Input("gene_dropdown_0", "value"),
            #   Input('yaxis_type', 'value')
        ],
        [
            State("complete_partial_radio_explore", "value"),
            State("country_dropdown_0", "value"),
        ],
        prevent_initial_call=False,
    )
    # @cache.memoize()
    def update_upper_plot(
        click_data,
        mutations,
        method,
        reference_id,
        seqtech_list,
        dates,
        interval,
        genes,
        complete_partial_radio,
        countries,
    ):
        try:
            clicked_country = click_data["points"][0]["hovertext"]
        except TypeError:
            clicked_country = ""

        detail_plot_instance = DetailPlots(
            df_dict,
            date_slider,
            reference_id,
            complete_partial_radio,
            countries,
            seqtech_list,
            mutations,
            dates,
            interval,
            color_dict,
            location_coordinates,
            genes,
            clicked_country,
        )
        title_text = f"Detailed look at the sequences with the chosen mutations for the selected \
                     country: {detail_plot_instance.location_name}"
        info_header = f"Number sequences for country {detail_plot_instance.location_name} and \
            selected properties between {detail_plot_instance.dates[0]} - \
            {detail_plot_instance.dates[-1]}: {detail_plot_instance.number_selected_sequences} of \
             which {detail_plot_instance.seq_with_mut} sequences carry at least one of the \
            selected mutations."
        # 1. plot
        if method == "Increase":
            fig = detail_plot_instance.create_slope_bar_plot()
            plot_header = "Slope mutations"
        elif method == "Frequency":
            fig = detail_plot_instance.get_frequency_bar_chart()
            plot_header = "Number Sequences"
        return fig, title_text, plot_header, info_header

    @callback(
        Output("mutation_development", "figure"),
        [
            Input("world_map_explorer", "clickData"),
            Input("mutation_dropdown_0", "value"),
            Input("reference_radio_0", "value"),
            Input("seq_tech_dropdown_0", "value"),
            Input("date_slider", "value"),
            Input("selected_interval", "value"),
            Input("results_per_location", "clickData"),
            Input("complete_partial_radio_explore", "value"),
            Input("country_dropdown_0", "value"),
            Input("gene_dropdown_0", "value"),
        ],
        prevent_initial_call=True,
    )
    def update_lower_plot(
        click_data,
        mutations,
        reference_id,
        seqtech_list,
        dates,
        interval,
        click_data_box_plot,
        complete_partial_radio,
        countries,
        genes,
    ):
        if ctx.triggered_id == "results_per_location":
            mutations = [click_data_box_plot["points"][0]["label"]]
        try:
            clicked_country = click_data["points"][0]["hovertext"]
        except TypeError:
            clicked_country = ""

        detail_plot_instance = DetailPlots(
            df_dict,
            date_slider,
            reference_id,
            complete_partial_radio,
            countries,
            seqtech_list,
            mutations,
            dates,
            interval,
            color_dict,
            location_coordinates,
            genes,
            clicked_country,
        )
        fig_develop = detail_plot_instance.get_frequency_development_scatter_plot()
        return fig_develop

    # fill table
    @callback(
        [
            Output(component_id="table_explorer", component_property="data"),
            Output(component_id="table_explorer", component_property="columns"),
        ],
        [
            Input("mutation_dropdown_0", "value"),
            Input("reference_radio_0", "value"),
            Input("seq_tech_dropdown_0", "value"),
            Input("selected_interval", "value"),
            Input("date_slider", "value"),
            Input("country_dropdown_0", "value"),
            Input("complete_partial_radio_explore", "value"),
        ],
        prevent_initial_call=False,
    )
    # @cache.memoize()
    def update_table_filter(
        mutation_list,
        reference_id,
        seq_tech_list,
        interval,
        dates,
        countries,
        complete_partial_radio,
    ):
        date_list = date_slider.get_all_dates_in_interval(dates, interval)
        if mutation_list is None:
            mutation_list = []
        if seq_tech_list is None:
            seq_tech_list = []
        if date_list is None:
            date_list = []
        if countries is None:
            countries = []
        if reference_id is None:
            reference_id = sorted(list(df_dict["variantView"]["complete"].keys()))[0]

        table_explorer = TableFilter("explorer", mutation_list)
        table_df = table_explorer.create_explore_table(
            df_dict,
            complete_partial_radio,
            seq_tech_list,
            reference_id,
            date_list,
            countries,
        )
        return table_df.to_dict("records"), [
            {"name": i, "id": i} for i in table_df.columns
        ]
