import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc

from pages.util_help_tables import table
from pages.util_help_tables import table_1
from pages.util_help_tables import table_2

dash.register_page(__name__, path="/Help")

layout = (
    html.Div(
        children=[
            html.H2(children="MpoxRadar Help Page:", style={"textAlign": "center"}),
            html.Div(
                children="""
                MpoxRadar is a website visualising the distribution of mpox mutations and allowing the user to filter which information they are interested in having visualised. The website also allows the download of the selected filter of information. In the following section, you will see an explanation for each functionality and section of the “Tool” page of our website. Followed by a section dedicated to answering frequently asked questions (FAQ) and a description of the tested browser compatibility of our website.
            """,
                style={"textAlign": "center"},
            ),
            html.Br(),
            html.Div(
                children="""
                Functionalities from MpoxRadar explained:
            """,
                style={"margin-left": "10px"},
            ),
            # html.Img(
            #     src="assets/example_ReferenceGenome.png",
            #     style={
            #         "float": "right",
            #         "width": "100%",
            #         "max-width": "200px",
            #         "height": "auto",
            #     },
            # ),
            html.Ul(
                [
                    html.Li(
                        [html.Strong("Reference genomes:")],
                        style={"margin-left": "10px"},
                    ),
                    html.Ul(
                        [
                            html.Li(
                                [
                                    html.Div(
                                        """
                                       Here you see a list of reference genomes to choose from. As mpox has no unanimously defined reference genome (given its widespread and different clusters), we allow users to choose a reference genome from which the mutations will be calculated."""
                                    )
                                ]
                            ),
                            html.Li(
                                [
                                    "There are currently three options available for this field:"
                                ]
                            ),
                            html.Ul(
                                [
                                    html.Li(
                                        [
                                            html.Strong("NC_063383.1"),
                                            """ This genome is one of the reference genomes pointed out by the National Center for Biotechnology Information """,
                                            "(",
                                            dcc.Link(
                                                html.A("NCBI"),
                                                href="https://www.ncbi.nlm.nih.gov/",
                                                target="_blank",
                                            ),
                                            "): ",
                                            dcc.Link(
                                                href="https://www.ncbi.nlm.nih.gov/genomes/GenomesGroup.cgi?taxid=10244",
                                                target="_blank",
                                            ),
                                            ".",
                                        ]
                                    ),
                                    html.Li(
                                        [
                                            html.Strong("ON563414.1"),
                                            """ USA Center for Disease Control sequence (as stated """,
                                            dcc.Link(
                                                html.A("here"),
                                                href="https://labs.epi2me.io/basic-monkeypox-workflow/#workflow-steps",
                                                target="_blank",
                                            ),
                                            "). ",
                                        ]
                                    ),
                                    html.Li(
                                        [
                                            html.Strong("MT903344.1"),
                                            """ Mpox virus isolate MPXV-UK_P2 (as stated """,
                                            dcc.Link(
                                                html.A("here"),
                                                href="https://labs.epi2me.io/basic-monkeypox-workflow/#workflow-steps",
                                                target="_blank",
                                            ),
                                            "). ",
                                        ]
                                    ),
                                ]
                            ),
                            html.Li(
                                "The user can choose any reference genome from this list. If none is chosen, we will show the mutations compared to all reference genomes. "
                            ),
                            html.Li("The default reference genome is NC_063383.1"),
                        ]
                    ),
                    # html.Img(
                    #     src="assets/example_MutationsDisplayed.png",
                    #     style={
                    #         "float": "right",
                    #         "width": "100%",
                    #         "max-width": "200px",
                    #         "height": "auto",
                    #     },
                    # ),
                    html.Li(html.Strong("Mutations:")),
                    html.Ul(
                        [
                            html.Li(
                                [
                                    "After choosing one reference genome, this list will be updated with the available list of mutations."
                                ]
                            ),
                            html.Li(
                                [
                                    "The user can choose as many mutations from the list as they like to have visualised on the plot. "
                                ]
                            ),
                            html.Li(
                                [
                                    "In order to allow for easy access to choosing all mutations, there is always an option to choose “",
                                    html.Strong("all"),
                                    "”, which is also the option chosen by default.",
                                ]
                            ),
                        ]
                    ),
                    html.Li(html.Strong("Visualisation methods:")),
                    html.Ul(
                        [
                            html.Li(
                                [
                                    "The user can choose between the following four visualisation methods"
                                ]
                            ),
                            html.Ul(
                                [
                                    html.Li(
                                        [
                                            html.Strong("Frequencies"),
                                            """ with this option, you can visualise the frequency of mutations in different locations. The bigger the size of the shown bubble, the higher the frequency of the mutation there. """,
                                        ]
                                    ),
                                    html.Li(
                                        [
                                            html.Strong(
                                                "Increasing / Decreasing / Constant trend"
                                            ),
                                            """ with one of these options, you can visualise the trend of the mutations growth. These are calculated using linear regression in the backend. """,
                                        ]
                                    ),
                                ]
                            ),
                            html.Li(
                                "The user can choose exactly one visualisation method from this list. "
                            ),
                            html.Li("The default is to show frequencies."),
                        ]
                    ),
                    html.Li(html.Strong("Sequencing Technology used:")),
                    html.Ul(
                        [
                            html.Li(
                                [
                                    "You can choose which seuqncing technologies you want to see on the map. Given that this field is an optional field to fill for sequence uploaders, it is not always filled. Please keep that in mind while using this filter."
                                ]
                            ),
                            html.Li(
                                [
                                    "In order to allow for easy access to choosing all technologies, there is always an option to choose “",
                                    html.Strong("all"),
                                    "”, which is also the option chosen by default.",
                                ]
                            ),
                        ]
                    ),
                    html.Li(
                        [
                            "Users can also directly give in a ",
                            html.Strong("query using the MpoxSonar notation"),
                            ". You can read more about the possible commands below.",
                        ]
                    ),
                    html.Li(html.Strong("Map:")),
                    html.Ul(
                        [
                            html.Li(
                                [
                                    "The interactive map shows the spatial distribution of selected mutations within a given time span. If mutations are present, the plot displays a central data point for each country."
                                ]
                            ),
                            html.Li(
                                [
                                    "Clicking on a data point triggers the subplots to show additional information about the mutation distribution and the time course of the mutation frequencies for a specific region.",
                                ]
                            ),
                        ]
                    ),
                    html.Li(
                        [
                            "Users can press the “",
                            html.Strong("Play button"),
                            "” to see the visualisations of each day one after the other.",
                        ]
                    ),
                    html.Li(
                        [
                            "Furthermore, the query results can be shown as a table by pressing the “Show results in a table” button."
                        ]
                    ),
                    html.Li(
                        [
                            "The result are also downloadable using the button “",
                            html.Strong("Download results as a csv file"),
                            "”. With this function, we want to empower other scientists to conduct further research. ",
                        ]
                    ),
                ]
            ),
            html.H4(
                children="""
                MpoxSonar command - user manual
            """
            ),
            html.P(
                "MpoxRadar provides an interactive map and informative data to explore and understand current mpox data. It builds on top of MpoxSonar and integrates closely with many reliable python libraries and data structures. MpoxSonar is an extension of Covsonar (the database-driven system for handling genomic sequences of SARS-CoV-2 and screening genomic profiles, developed at the RKI (https://github.com/rki-mf1/covsonar)) that adds support for multiple genome references and quick processing with MariaDB.  Hence, with MpoxSonar as the backend, we can quickly collect mutation profiles from sequence data. Currently, the MpoxRadar provides the feature to interact with MpoxSonar for a specific type of query."
            ),
            html.P(
                "Due to security reason, we limit some MpoxSonar commands to be accessible. The following commands are currently available in MpoxRadar website;"
            ),
            table_2,
            html.Li(
                [
                    html.Strong("Reminder"),
                    ": Currently, we provide three reference genomes; including, NC_063383.1, ON563414.3 and MT903344.1. However, they annotate gene and protein names differently. For example, NC_063383 uses the “OPGXXX” tag (e.g., OPG003, OPG019), while ON563414.3 uses the “MPXV-USA” tag. This can affect a protein search and result in querying the same mutation profile. ( ",
                    html.Strong("MPXV-USA_2022_MA001-164:L246F"),
                    " vs. ",
                    html.Strong("OPG188:L246F"),
                    " ).",
                ]
            ),
            html.H3(
                children="""
                FAQ:
            """,
                style={"marginTop": "25px", "textAlign": "center"},
            ),
            html.Div(
                children="""
                What is genome?
            """
            ),
            html.Li(
                [
                    """
                A genome is all the genetic information of an organism, which contains blueprints for proteins. It consists of nucleotide sequences of DNA (or RNA in RNA viruses) in an organism.""",
                    html.Br(),
                    """A nucleotide is a unit that makes up a nucleic acid. Nucleotide names are indicated by a four-letter code: Adenine(A), Cytosine(C), Thymine(T), Guanine(G). And the polymer of nucleotides is RNA. When three consecutive nucleotide units come together, it is called a codon, and this codon structure represents the 20 amino acids that make up a protein.""",
                ]
            ),
            html.Br(),
            html.Div(
                children="""
                What is a mutation?
            """
            ),
            html.Li(
                [
                    """
                A mutation is a change in the sequence of genetic information, which is caused by errors in replication. These changes can lead to a change in nucleotides, which in turn can lead to changes in amino acids. Amino acids form proteins and these have a variety of functions in the organism. Principally, there are two types of genetic variation: The one is SNP(Single Nucleotide Polymorphism), and the other is INDEL(Insertion & Deletion). SNP is a mutation in which a single nucleotide is changed. INDEL is a mutation, when plural nucleotides are inserted or deleted in comparison with a reference sequence.""",
                    html.Br(),
                    """For instance, C162331T appears as a lineage change of aminoacid from C to T in position 162331.""",
                    html.Br(),
                    """A mutation is usually deleterious to the virus, causing that mutation to die out, but sometimes it can lead to benefits (such as increased infectivity, vaccine escape, antibody escape, etc.), which is deleterious for the host. That's why genomic surveillance is so important.""",
                ]
            ),
            html.Br(),
            html.Div(
                children="""
                Why do we have multiple references? What changes when you change the reference?
            """
            ),
            html.Li(
                [
                    "To support mutation analysis in different locations and times. A reference genome is an idealized representative or template of the collection of genes in one species at a certain time. With advancements in technology, the reference genome is continually refined and filled the gap of inaccuracies represented in the reference genome. This is imperative because selecting a genome reference may affect subsequent analysis, such as detecting single nucleotide polymorphisms (SNPs), phylogenetic inference, functional prediction or defining the source of errors.",
                    html.Br(),
                    "Moreover, genes are more divergent, and they are often affected by interactions with the environment, for example, temperature, pollutants or exposure to some interference that alters a transcription or replication process. So, permanent changes can be made to the genetic code of a gene as a result of these effects. When we perform DNA sequencing for the reference genome, a new DNA change might exist in the reference genome throughout time.",
                    html.Br(),
                    "Therefore, technological improvements have led to the release of reference genomes over time and annotations with better well-studied approaches, and the choice of a reference genome can improve the quality and accuracy of the downstream analysis.",
                ]
            ),
            html.Br(),
            html.Div(
                children="""
                What changes when you change the reference?
            """
            ),
            html.Li(
                [
                    "Even though the new releases of genome assembly shares significant amounts of synteny with the previous version, the annotated structure of genes or individual bases in the same regions can differ.  ",
                    html.Br(),
                    "This change might affect",
                    html.Ol(
                        [
                            html.Li("variant identification"),
                            html.Li("new or re-annotated coding sequences (CDS)"),
                            html.Li("identifier of gene and protein"),
                            html.Li(
                                [
                                    "variant identification",
                                    "(for more details, ",
                                    dcc.Link(
                                        href="https://www.ncbi.nlm.nih.gov/genomes/locustag/Proposal.pdf",
                                        target="_blank",
                                    ),
                                    " )",
                                ],
                                style={"listStyleType": "none"},
                            ),
                        ]
                    ),
                ]
            ),
            html.Br(),
            html.Div(
                children="""
                How often the application gets updated?
            """
            ),
            table_1,
            html.Br(),
            html.H4(
                children="""
                Browser compatibility
            """
            ),
            dbc.Table(table),
            html.Div(
                children="""
                Note that these are the browser versions we specifically used for testing. Older versions will likely also work. Mobile browsers and Internet Explorer are generally not supported.
            """
            ),
        ],
    ),
)
