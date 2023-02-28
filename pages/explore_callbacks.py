from dash import callback
from dash import Input
from dash import Output
from dash import State
from dash import ctx
from dash.exceptions import PreventUpdate

from pages.utils_filters import get_all_frequency_sorted_countries_by_filters, actualize_filters
from pages.utils_filters import get_all_gene_dict
from pages.utils_filters import get_frequency_sorted_mutation_by_filters
from pages.utils_filters import get_frequency_sorted_seq_techs_by_filters
from pages.utils_worldMap_explorer import DateSlider
from pages.utils_worldMap_explorer import WorldMap
from pages.utils_worldMap_explorer import TableFilter


# This is the EXPLORE TOOL PART
def get_explore_callbacks(  # noqa: C901
        df_dict,
        date_slider,
        color_dict,
        location_coordinates
):
    @callback(
        [
            Output("mutation_dropdown_0", "options"),
            Output("mutation_dropdown_0", "value"),
            Output("max_nb_txt_0", "children"),
            Output("select_x_frequent_mut_0", "max"),
            Output("select_x_frequent_mut_0", "value"),
        ],
        [
            Input("reference_radio_0", "value"),
            Input("gene_dropdown_0", "value"),
            Input("seq_tech_dropdown_0", "value"),
            Input("country_dropdown_0", "value"),
            Input("select_x_frequent_mut_0", "value"),
            Input("complete_partial_radio_explore", "value"),
        ],
        [
            State("mutation_dropdown_0", "options"),
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
            mut_options,
    ):
        # TODO now return top x mut without checking for mutations with same number
        if ctx.triggered_id == "select_x_frequent_mut_0":
            mut_value = [i["value"] for i in mut_options[0:select_x_mut]]
            max_select = len(mut_options)

        else:
            mut_options = get_frequency_sorted_mutation_by_filters(
                df_dict,
                seqtech_value,
                country_value,
                gene_value,
                complete_partial_radio,
                reference_value,
                color_dict
            )
            max_select = len(mut_options)
            if len(mut_options) < 20:
                select_x_mut = len(mut_options)
            else:
                select_x_mut = 20
            mut_value = [i["value"] for i in mut_options][0:select_x_mut]

        text = (
            f"Select x most frequent sequences. Maximum number of mutations (including unique mutations) with chosen "
            f"filter options: {len(mut_options)}"
        )
        return mut_options, mut_value, text, max_select, select_x_mut

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
            'cds',
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
            seq_tech_value
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
            Input("gene_dropdown_0", "value"),
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
            genes,
            complete_partial_radio,
            layout,
    ):
        date_list = date_slider.get_all_dates_in_interval(dates, interval)
        world_map_dfs = [df_dict["world_map"]['complete'][reference_id]]
        if complete_partial_radio == 'partial':
            world_map_dfs.append(df_dict["world_map"]['partial'][reference_id])
        world_map = WorldMap(world_map_dfs, color_dict, location_coordinates)
        fig = world_map.get_world_map(
            mutation_list,
            seqtech_list,
            method,
            date_list,
            countries,
            genes,
        )
        # layout: {'geo.projection.rotation.lon': -99.26450411962647, 'geo.center.lon': -99.26450411962647,
        # 'geo.center.lat': 39.65065298875763, 'geo.projection.scale': 2.6026837108838667}
        # TODO sometimes not working
        if layout:
            fig.update_layout(layout)
        return fig

    @callback(
        Output("date_slider", "value"),
        [
            Input("date_slider", "drag_value"),
            Input("selected_interval", "value"),
            Input("auto_stepper", "n_intervals"),
        ],
        [
            State("date_slider", "value"),
        ],
        prevent_initial_call=True,
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
        if ctx.triggered_id == "auto_stepper":
            if n_intervals == 0:
                # raise PreventUpdate
                return slider_value
            if interval is None:
                interval = 7
            if n_intervals + interval >= len(date_slider.date_list):
                first_date = DateSlider.unix_time_millis(
                    date_slider.date_list[-interval]
                )
                second_date = DateSlider.unix_time_millis(date_slider.date_list[-1])
            else:
                first_date = DateSlider.unix_time_millis(
                    date_slider.date_list[n_intervals - 1]
                )
                second_date = DateSlider.unix_time_millis(
                    date_slider.date_list[n_intervals + interval - 1]
                )  # first_date + interval*86400
            return [first_date, second_date]

    @callback(
        [
            Output("auto_stepper", "max_intervals"),
            Output("auto_stepper", "disabled"),
            Output("play_button", "className"),
        ],
        [
            Input("play_button", "n_clicks"),
            Input("auto_stepper", "n_intervals"),
        ],
        [State("selected_interval", "value"), State("play_button", "className")],
        prevent_initial_call=True,
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
        if ctx.triggered_id == "play_button":
            # start stepper
            if button_icon == "fa-solid fa-circle-play fa-lg":
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
            Output("results_per_location", "figure"),
            Output("chosen_location", "children"),
            Output("header_upper_plot", "children"),
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
            Input("complete_partial_radio_explore", "value"),
            Input("country_dropdown_0", "value"),
            #   Input('yaxis_type', 'value')
        ],
        prevent_initial_call=True,
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
            countries
    ):
        try:
            location_name = click_data["points"][0]["hovertext"]
        except TypeError:
            if countries:
                location_name = countries[0]
            else:
                location_name = None
        if location_name and location_name not in countries:
            location_name = countries[0]
        # date from slider
        date_list = date_slider.get_all_dates_in_interval(dates, interval)
        # title text
        title_text = location_name if location_name else ""
        world_dfs = [df_dict["world_map"]['complete'][reference_id]]
        if complete_partial_radio == 'partial':
            world_dfs.append(df_dict["world_map"]['partial'][reference_id])
        world_map = WorldMap(world_dfs, color_dict, location_coordinates)
        # 1. plot
        if method == "Increase":
            fig = world_map.get_slope_bar_plot(
                date_list, mutations, seqtech_list, location_name, genes
            )
            plot_header = "Slope mutations"
        elif method == "Frequency":
            fig = world_map.get_frequency_bar_chart(
                mutations, seqtech_list, date_list, location_name, genes
            )
            plot_header = "Number Sequences"
        return fig, title_text, plot_header

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
            Input("gene_dropdown_0", "value"),
            Input("complete_partial_radio_explore", "value"),
            Input("country_dropdown_0", "value"),
        ],
        prevent_initial_call=True,
    )
    def update_lower_plot(
            click_data_map,
            mutations,
            reference_id,
            seqtech_list,
            dates,
            interval,
            clickDataBoxPlot,
            genes,
            complete_partial_radio,
            countries
    ):
        if ctx.triggered_id == "results_per_location":
            mutations = [clickDataBoxPlot["points"][0]["label"]]
        try:
            location_name = click_data_map["points"][0]["hovertext"]
        except TypeError:
            if countries:
                location_name = countries[0]
            else:
                location_name = None
        if location_name and location_name not in countries:
            location_name = countries[0]
        date_list = date_slider.get_all_dates_in_interval(dates, interval)
        world_dfs = [df_dict["world_map"]['complete'][reference_id]]
        if complete_partial_radio == 'partial':
            world_dfs.append(df_dict["world_map"]['partial'][reference_id])
        world_map = WorldMap(world_dfs, color_dict, location_coordinates)
        fig_develop = world_map.get_frequency_development_scatter_plot(
            mutations, seqtech_list, date_list, location_name, genes
        )
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
            Input("gene_dropdown_0", "value"),
            Input("country_dropdown_0", "value"),
            Input("complete_partial_radio_explore", "value"),
        ],
        prevent_initial_call=True,
    )
    # @cache.memoize()
    def update_table_filter(
            mutation_list,
            reference_id,
            seq_tech_list,
            interval,
            dates,
            gene_values,
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
            reference_id = sorted(list(df_dict["variantView"]['complete'].keys()))[0]

        table_explorer = TableFilter()
        table_df = table_explorer.get_filtered_table(
            df_dict,
            complete_partial_radio,
            mutation_list,
            seq_tech_list,
            reference_id,
            date_list,
            gene_values,
            countries,
        )
        return table_df.to_dict("records"), [
            {"name": i, "id": i} for i in table_df.columns
        ]
