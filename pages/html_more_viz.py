import logging
from dash import dash_table
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from data_management.data_manager import DataManager
data_manager = DataManager.get_instance()

def create_TRIMTSIG_graph():  #
    mutation_signature = data_manager.calculate_tri_mutation_sig()
    fig = make_subplots(
        rows=3,
        cols=1,
        subplot_titles=[accession for accession in mutation_signature.keys()],
        # x_title='Base substitutions',
        y_title="Contributions",
    )

    for i, accession in enumerate(mutation_signature.keys()):
        labels = []
        values = []
        for mutation_type in mutation_signature[accession]:
            # Create a list of labels
            labels.extend(
                [_type for _type in mutation_signature[accession][mutation_type]]
            )
            values.extend(
                [
                    mutation_signature[accession][mutation_type][_type]
                    for _type in mutation_signature[accession][mutation_type]
                ]
            )

        # Create a trace for each accession
        trace = go.Bar(x=labels, y=values, name=accession)
        fig.add_trace(trace, row=i + 1, col=1)

    # Update the layout for the plot
    fig.update_layout(
        height=800,
        autosize=True,
        showlegend=False,
    )
    fig.update_xaxes(
        tickangle=-45,  # rotate the labels
        tickfont=dict(size=10),  # set the font size of the labels
    )
    # fig.update_layout(annotations=[dict(xshift=-60)])

    return fig


# Create a bar plot to visualize the mutation signature
def create_MTSIG_graph():  #
    mutation_signature = data_manager.calculate_mutation_sig()
    # Define the color scheme
    colors = [
        "rgb(252,141,98)",
        "rgb(102,194,165)",
        "rgb(141,160,203)",
        "rgb(231,138,195)",
        "rgb(166,216,84)",
        "rgb(255,217,47)",
        "rgb(229,196,148)",
        "rgb(179,179,179)",
        "rgb(255,255,255)",
    ]

    # Create a list of labels
    labels = ["C>A", "C>G", "C>T", "T>A", "T>C", "T>G"]

    # Create a figure with three subplots, one for each accession
    fig = make_subplots(
        rows=1,
        cols=3,
        subplot_titles=[accession for accession in mutation_signature.keys()],
    )

    # Create a trace for each accession
    for i, accession in enumerate(mutation_signature.keys()):
        try:
            values = [mutation_signature[accession][label] for label in labels]
        except KeyError:
            logging.warning(f"KeyError: {accession} not found in mutation_signature")
            continue
        trace = go.Bar(x=labels, y=values, name=accession, marker=dict(color=colors))
        fig.add_trace(trace, row=1, col=i + 1)

    # Update the layout for the plot
    fig.update_layout(
        title="",
        xaxis=dict(title="Base substitutions"),
        yaxis=dict(title="Contributions"),
        showlegend=False,
    )

    return fig


snp_table_df = data_manager.create_snp_table()

mataion_signature_layout = html.Div(
    [
        dbc.Card(
            [
                dbc.CardHeader("Mutational Signature Analysis"),
                dbc.CardBody(
                    [
                        dbc.Row(dbc.Col(html.H3("Mutation signature"))),
                        dbc.Row(
                            dbc.Col(
                                html.P(
                                    "Only consider six classes of base substitution: C>A, C>G, C>T, T>A, T>C and T>G.",
                                    className="mb-0",
                                ),
                            )
                        ),
                        dbc.Row(dbc.Col(dcc.Graph(figure=create_MTSIG_graph()))),
                        dbc.Row(
                            dbc.Col(
                                html.H3("Mutation signature: Trinucleotide context")
                            )
                        ),
                        dbc.Row(
                            dbc.Col(
                                html.P(
                                    "A total of 96 possible mutation types (e.g. A[C>A]A, A[C>A]T, etc.).",
                                    className="mb-0",
                                ),
                            )
                        ),
                        dbc.Row(
                            dbc.Col(
                                [
                                    html.I(
                                        className="fa-solid fa-computer-mouse",
                                    ),
                                    dbc.FormText(
                                        " Note:Please use the zoom-in button, click and drag from the centre of the x-axis to see all labels.",
                                        color="primary",
                                    ),
                                ],
                            ),
                        ),
                        dbc.Row(dbc.Col(dcc.Graph(figure=create_TRIMTSIG_graph()))),
                        dbc.Row(dbc.Col(html.H3("Free Search"))),
                        dbc.Row(
                            dbc.Col(
                                [
                                    dash_table.DataTable(
                                        data=snp_table_df.to_dict("records"),
                                        columns=[
                                            {"id": c, "name": c}
                                            for c in snp_table_df.columns
                                        ],
                                        filter_action="native",
                                        sort_action="native",
                                        sort_mode="multi",
                                        page_size=20,  # we have less data in this example, so setting to 20
                                        style_table={
                                            "height": "300px",
                                            "overflowY": "auto",
                                        },
                                    )
                                ],
                            ),
                        ),
                    ]
                ),
            ]
        ),
    ]
)

tab_more_tool = [
    dbc.Row(dbc.Col(html.H2("More Viz Tool ", style={"textAlign": "center"}))),
    mataion_signature_layout,
]
