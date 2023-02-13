from dash import html
import dash_bootstrap_components as dbc


# Table for Browser compatibility

table_header = [
    html.Thead(
        html.Tr(
            [
                html.Th("OS"),
                html.Th("Version"),
                html.Th("Chrome"),
                html.Th("Firefox"),
                html.Th("Microsoft Edge"),
                html.Th("Safari"),
            ]
        )
    )
]

row1 = html.Tr(
    [
        html.Td("Linux"),
        html.Td("Ubuntu 22.04.1 LTS"),
        html.Td("108.0.5359.124"),
        html.Td("108.0.1"),
        html.Td("n/a"),
        html.Td("n/a"),
    ]
)
row2 = html.Tr(
    [
        html.Td("MacOS"),
        html.Td("HighSierra"),
        html.Td("Not tested"),
        html.Td("Not tested"),
        html.Td("n/a"),
        html.Td("Not tested"),
    ]
)
row3 = html.Tr(
    [
        html.Td("Windows"),
        html.Td("10"),
        html.Td("108.0.5359.124"),
        html.Td("102.4.0esr"),
        html.Td("108.0.1462.54"),
        html.Td("n/a"),
    ]
)

table_body = [html.Tbody([row1, row2, row3])]

table = dbc.Table(
    table_header + table_body,
    bordered=True,
    style={
        "width": "100%",
        "marginTop": "10px",
        "margin-left": "auto",
        "marginRight": "auto",
    },
    className="relative",
)

# Table for FAQ How often the application gets updated?
table_header_1 = [
    html.Thead(
        html.Tr(
            [
                html.Th("Type"),
                html.Th("What"),
                html.Th("Update frequency"),
            ]
        )
    )
]

row_1 = html.Tr(
    [
        html.Td("Data in the database"),
        html.Td("Add new sequence&metadata or update from existing sources"),
        html.Td("Daily"),
    ]
)
row_2 = html.Tr(
    [
        html.Td("MPoxRadar"),
        html.Td("major/minor updates"),
        html.Td("When required"),
    ]
)
row_3 = html.Tr(
    [
        html.Td("MPoxSonar"),
        html.Td("major/minor updates"),
        html.Td("When required"),
    ]
)

table_body_1 = [html.Tbody([row_1, row_2, row_3])]

table_1 = dbc.Table(
    table_header_1 + table_body_1,
    bordered=True,
    style={"width": "80%", "marginTop": "10px"},
    className="relative",
)


# Table for user command


table_header_2 = [
    html.Thead(
        html.Tr(
            [
                html.Th("Description"),
                html.Th("Example command"),
            ]
        )
    )
]

row_d = html.Tr(
    [
        html.Td("Select all samples from reference 'NC_063383.1' and in USA"),
        html.Td("match -r NC_063383.1 --COUNTRY USA"),
    ]
)

row_e = html.Tr(
    [
        html.Td(
            "Select all samples that have range from 1 to 60 of deletion mutation (e.g., del:1-60, del:1-6, del:11-20)."
        ),
        html.Td("match --profile del:1-60"),
    ]
)

row_f = html.Tr(
    [
        html.Td(
            "Select all samples except samples contain C162331T mutation (‘^’ = exclude/neglect)"
        ),
        html.Td("match --profile ^C162331T"),
    ]
)

row_g = html.Tr(
    [
        html.Td(
            [
                html.Div(
                    "Combine with 'OR' search; for example, get all samples that have mutation at L246F in all references."
                ),
                html.Div("In our case;"),
                html.Li(
                    [
                        html.Span("OPG188", style={"color": "blue"}),
                        ": ",
                        html.Strong("L246F"),
                        " for NC_063383",
                    ]
                ),
                html.Li(
                    [
                        html.Span("MPXV-UK_P2-164", style={"color": "blue"}),
                        ": ",
                        html.Strong("L246F"),
                        " for MT903344.1",
                    ]
                ),
                html.Li(
                    [
                        html.Span("MPXV-USA_2022_MA001-164", style={"color": "blue"}),
                        ": ",
                        html.Strong("L246F"),
                        " for ON563414.3",
                    ]
                ),
                html.Div("(provide --profile tag separately)"),
            ]
        ),
        html.Td(
            [
                html.Div("match --profile OPG188:L246F --profile"),
                html.Div("MPXV-UK_P2-164:L246F --profile"),
                html.Div("MPXV-USA_2022_MA001-164:L246F"),
            ]
        ),
    ]
)

row_h = html.Tr(
    [
        html.Td(
            [
                html.Strong("'AND'"),
                " operation; for example, get all samples that have mutation at ",
                html.Strong("A151461C and exact 1-6 deletion"),
                "(concate a query at same --profile)",
            ]
        ),
        html.Td("match --profile A151461C del:=1-=6"),
    ]
)

row_i = html.Tr(
    [
        html.Td(
            "Select all samples from sequence length in a range between 197120 and 197200 base pairs"
        ),
        html.Td("match --LENGTH >197120 <197200"),
    ]
)

row_j = html.Tr(
    [
        html.Td("Get sample by name."),
        html.Td("match --sample ON585033.1"),
    ]
)


table_body_2 = [html.Tbody([row_d, row_e, row_f, row_g, row_h, row_i, row_j])]

table_2 = dbc.Table(
    table_header_2 + table_body_2,
    bordered=True,
    style={"width": "100%", "marginTop": "10px"},
    className="relative",
)

cheatsheet_header = [
    html.Thead(
        html.Tr(
            [
                html.Th(" "),
                html.Th("Description"),
                html.Th("Example command"),
            ]
        )
    )
]

row1 = html.Tr(
    [
        html.Td("list property"),
        html.Td("View all properties in the database."),
        html.Td("list-prop"),
    ]
)
row2 = html.Tr(
    [
        html.Td("Query sequence"),
        html.Td(
            "We use 'match' coommand to query genome sequences based on profiles or properties. (by default, match command will get all mutation profiles from database.)"
        ),
        html.Td("match"),
    ]
)
row3 = html.Tr(
    [
        html.Td("Query sequence with defined reference"),
        html.Td(
            "Define reference accession to query sample with a specific reference."
        ),
        html.Td("match -r NC_063383.1 "),
    ]
)
row4 = html.Tr(
    [
        html.Td("Query SNP profile"),
        html.Td(
            "For NT: ref_nuc followed by ref_pos followed by alt_nuc (e.g. T28175C). For AA: protein_symbol:ref_aa followed by ref_pos followed by alt_aa (e.g. OPG098:E162K)"
        ),
        html.Td("match --profile T28175C"),
    ]
)
row5 = html.Tr(
    [
        html.Td("Query DEL profile"),
        html.Td(
            "For NT: del:first_NT_deleted-last_NT_deleted (e.g. del:133177-133186). For AA: protein_symbol:del:first_AA_deleted-last_AA_deleted (e.g. OPG197:del:34-35)"
        ),
        html.Td("match --profile del:133177-133186"),
    ]
)
row6 = html.Tr(
    [
        html.Td("Query INS profile"),
        html.Td(
            "For NT: ref_nuc followed by ref_pos followed by alt_nucs (e.g. T133102TTT). For AA: protein_symbol:ref_aa followed by ref_pos followed by alt_aas (e.g. OPG197:A34AK)"
        ),
        html.Td("match --profile OPG197:A34AK"),
    ]
)
row7 = html.Tr(
    [
        html.Td("Count result"),
        html.Td("Count result from a given query."),
        html.Td("match -r NC_063383.1 --count"),
    ]
)
row8 = html.Tr(
    [
        html.Td("NOT query"),
        html.Td(
            "Use ^ as a 'NOT' operator. We put it before any conditional statement to negate, exclude or filter the result."
        ),
        html.Td("sonar match -r NC_063383.1 --COLLECTION_DATE ^2022-01-01"),
    ]
)

row9 = html.Tr(
    [
        html.Td(["Match profile with ", html.Strong("OR"), " operation"]),
        html.Td("matches genomes having the xxx OR xxx profiles  (seperate --profile)"),
        html.Td("match --profile  del:133177-133186 --profile OPG197:del:34-35"),
    ]
)

row10 = html.Tr(
    [
        html.Td(["Match profile with ", html.Strong("AND"), " operation"]),
        html.Td("matches genomes having the xxx AND xxx profiles"),
        html.Td("match --profile OPG044:L29P T28175C"),
    ]
)
# DATE
row11 = html.Tr(
    [
        html.Td("Date data type"),
        html.Td("Query with date range XXXX:XXXX"),
        html.Td("match  --COLLECTION_DATE 2020-01-01:2020-12-31"),
    ]
)
#
row12 = html.Tr(
    [
        html.Td("Int data type"),
        html.Td("Query with comparison operators (e.g., >, !=, <, >=, <=)"),
        html.Td("match --LENGTH >=197120 <197200"),
    ]
)

cheatsheet_body = [
    html.Tbody(
        [row1, row2, row3, row4, row5, row6, row7, row8, row9, row10, row11, row12]
    )
]

cheatsheet_table = dbc.Table(cheatsheet_header + cheatsheet_body, bordered=True)
