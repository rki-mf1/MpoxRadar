import dash
from dash import dcc
from dash import html

dash.register_page(__name__, path="/Imprint")

layout = (
    html.Div(
        children=[
            html.H3(children="Imprint"),
            html.Br(),
            html.H4(
                children="Information according to § 5 German Telemedia Act:",
                style={"marginBottom": "10px"},
            ),
            html.Div("Stephan Fuchs", style={"marginBottom": "10px"}),
            html.Div("Seestraße 10", style={"marginBottom": "10px"}),
            html.Div("13353 Berlin"),
            html.Br(),
            html.H4("Contact: "),
            dcc.Link(
                html.A("fuchsS@rki.de"), href="mailto:fuchsS@rki.de", target="_blank"
            ),
            html.Br(),
            html.Br(),
            html.Br(),
            html.H3(children="Privacy Policy:"),
            html.H4("1. Introductory Remarks"),
            html.P(
                [
                    "This page is used to inform website visitors regarding our policies with the collection, use, and disclosure of personal data if anyone decided to use our Service, the MpoxRadar website (",
                    dcc.Link(href="https://mpoxradar.net/", target="_blank"),
                    "). Personal data is information that makes it possible to identify a person. In addition to direct personal information, such as name, date of birth or telephone number or IP address, this also includes data on personal characteristics, beliefs or relationships that allow a conclusion to be drawn about a specific person. The operators of these pages take the protection of your personal data very seriously. We treat your personal data confidentially and according to the legal data protection regulations as well as this Privacy Policy. If you choose to use our Service, then you agree to the collection and use of information in relation with this policy. The personal information that we collect is used for providing and improving the Service. We will not use or share your information with anyone except as described in this Privacy Policy. We would like to point out that the data transmission on the Internet (e.g. communication by e-mail) can have security gaps. A complete protection of data against access by third parties is not possible.",
                ]
            ),
            html.H4("2. General Information on Data Processing"),
            html.P(
                "As a matter of principle, we collect and use personal data of our users only to the extent necessary for providing a functional website and service and as the legal requirements allow."
            ),
            html.H4("3. Contact Details"),
            html.Div("Hasso-Plattner-Institut", style={"marginBottom": "10px"}),
            html.Div("FG Bernhard Renard", style={"marginBottom": "10px"}),
            html.Div("Prof.-Dr.-Helmert-Straße 2 – 3", style={"marginBottom": "10px"}),
            html.Div("14482 Potsdam", style={"marginBottom": "10px"}),
            html.H4("4. Data Protection officer"),
            html.Div("Prof. Dr. Bernhard Renard", style={"marginBottom": "10px"}),
            html.H4("5. Purpose"),
            html.P(
                "The purpose of the MpoxRadar service is to provide insights into mutation frequency in public mpox genomes as well as temporal and spatial distributions of genomic mpox variants."
            ),
            html.H4("6. Scope of Data Processing"),
            html.H4("Storage of Browser Data"),
            html.P(
                "Whenever you visit our website, our system automatically collects data and information from the computer system of the calling computer. The following data is collected:"
            ),
            html.Ul(
                [
                    html.Li("Information about the browser type and the version used"),
                    html.Li("The user's operating system"),
                    html.Li("The Internet service provider of the user"),
                    html.Li("The IP address of the user"),
                    html.Li("Date and time of access"),
                    html.Li(
                        "Websites from which the user's system accesses our website"
                    ),
                    html.Li("Visited domain"),
                    html.Li("Timestamp of the visit"),
                    html.Li("Status code"),
                    html.Li("Size of the response body"),
                    html.Li("Referrer sent by the client"),
                    html.Li("User agent sent by the client"),
                ]
            ),
            html.P(
                "The data is also stored in the log files of our system, but not linked with any other personal data of the user. The temporary storage of the IP address by the system is necessary to enable the website to be delivered to the user's computer. For this purpose, the user's IP address must remain stored for the duration of the session. The storage in log files is done to ensure the functionality of the website. In addition, the data is used to optimize the website and to ensure the security of our information technology systems. An evaluation of the data for marketing purposes does not take place in this context. The data is deleted when the respective session is ended. If the data is stored in log files, it will be deleted after two weeks at the latest."
            ),
            html.H4("Use of Cookies"),
            html.P(
                "This website does not use cookies to collect personally identifiable information about you as a user of the site."
            ),
            html.H4("7. External Links"),
            html.P(
                "Our Service may contain links to other sites. If you click on a third-party link, you will be directed to that site. Note that these external sites are not operated by us. Therefore, we strongly advise you to review the Privacy Policy of these websites. We have no control over, and assume no responsibility for the content, privacy policies, or practices of any third-party sites or services."
            ),
            html.H4("8. Children's Privacy"),
            html.P(
                "Our Services do not address anyone under the age of 18. We do not knowingly collect personal data from children under 13. In the case we discover that a child under 18 has provided us with personal data, we immediately delete this from our servers. If you are a parent or guardian and you are aware that your child has provided us with personal information, please contact us so that we will be able to do necessary actions."
            ),
            html.H4("9. Your Rights"),
            html.P(
                "As a person concerned, you may at any time exercise the rights granted to you by the EU-DSGVO, insofar as they apply to the processing:"
            ),
            html.Ul(
                [
                    html.Li(
                        "the right to be informed whether and which of your data are being processed (Art. 15 DSGVO)"
                    ),
                    html.Li(
                        "the right to request the correction or completion of data concerning you (Art. 16 DSGVO)"
                    ),
                    html.Li(
                        "the right to have data relating to you deleted in accordance with Art. 17 DSGVO"
                    ),
                    html.Li(
                        "the right to request, in accordance with Art. 18 DPA, a restriction on the processing of data"
                    ),
                    html.Li(
                        "the right to object to future processing of data concerning you in accordance with Art. 21 DPA"
                    ),
                ]
            ),
            html.P(
                "The collection of data for the provision of the web offer and the storage of the data in log files is mandatory for the operation of the web pages. There is therefore no possibility of objection on the part of the user. Although IP addresses are regarded as personal data, they are not assigned to any person, so they cannot be assigned to any user and therefore cannot be accessed when information is requested. In addition to the aforementioned rights, you have the right to lodge a complaint with the data protection supervisory authority (Art. 77 DSGVO)."
            ),
            html.H4("10. Validity of this Privacy Policy"),
            html.P(
                [
                    "Unless otherwise specified in this privacy statement, the regulations of the de.NBI Privacy Policy (",
                    dcc.Link(
                        href="https://www.denbi.de/privacy-policy", target="_blank"
                    ),
                    ") apply. We may update our Privacy Policy from time to time. Thus, we advise you to review this page periodically for any changes. We will notify you of any changes by posting the new Privacy Policy on this page. These changes are effective immediately, after they are posted on this page. If you have any questions or suggestions about our Privacy Policy, do not hesitate to contact us.",
                ]
            ),
        ],
    ),
)
