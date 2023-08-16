from .libs.mpxsonar.src.mpxsonar.basics import sonarBasics
from .libs.mpxsonar.src.mpxsonar.dbm import sonarDBManager

import sys
import pandas as pd

# CLASS
class sonarBasicsChild(sonarBasics):
    """
    this class inherit from sonarBasics to provides sonarBasics functionalities and intelligence
    """

    # matching
    @staticmethod
    def match(
        db,
        profiles=[],
        reserved_props_dict={},
        propdict={},
        reference=None,
        outfile=None,
        output_column="all",
        format="csv",
        debug=False,
        showNX=False,
    ):
        output = None
        if outfile:
            output = """The current MpoxSonar in the MpoxRadar is
            not supporting the save-output-to-file command (-o). """
            return output

        with sonarDBManager(db, debug=debug) as dbm:
            if format == "vcf" and reference is None:
                reference = dbm.get_default_reference_accession()

            cursor = dbm.match(
                *profiles,
                reserved_props=reserved_props_dict,
                properties=propdict,
                reference_accession=reference,
                format=format,
                output_column=output_column,
                showNX=showNX,
            )
            if format == "csv" or format == "tsv":
                # cursor => list of dict
                df = pd.DataFrame(cursor)
                if "MODIFIED" in df.columns:
                    df.drop(["MODIFIED"], axis=1, inplace=True)
                # print(df)
                if len(df) == 0:
                    output = "*** no match ***"
                else:
                    output = df
                # tsv = True if format == "tsv" else False
                # sonarBasics.exportCSV(
                #    cursor, outfile=outfile, na="*** no match ***", tsv=tsv
                # )
            elif format == "count":
                output = cursor.fetchone()["count"]
            elif format == "vcf":
                # remove this export
                # sonarBasics.exportVCF(
                #     cursor, reference=reference, outfile=outfile, na="*** no match ***"
                # )
                output = """The current MpoxSonar in the MpoxRadar is not
                supporting the VCF command (--format vcf). """
            else:
                sys.exit("error: '" + format + "' is not a valid output format")

        return output

    def list_prop(db=None):
        output = ""
        with sonarDBManager(db, debug=False) as dbm:
            if not dbm.properties:
                print("*** no properties ***")
                exit(0)

            cols = [
                "name",
                "argument",
                "description",
                "data type",
                "query type",
                "standard value",
            ]
            rows = []
            for prop in sorted(dbm.properties.keys()):
                dt = (
                    dbm.properties[prop]["datatype"]
                    if dbm.properties[prop]["datatype"] != "float"
                    else "decimal number"
                )
                rows.append([])
                rows[-1].append(prop)
                rows[-1].append("--" + prop)
                rows[-1].append(fill(dbm.properties[prop]["description"], width=25))
                rows[-1].append(dt)
                rows[-1].append(dbm.properties[prop]["querytype"])
                rows[-1].append(dbm.properties[prop]["standard"])
            # output = tabulate(rows, headers=cols, tablefmt="orgtbl")
            # output = output + "\n"
            # output = output + "DATE FORMAT" + "\n"
            output = pd.DataFrame(rows, columns=cols)
            # remove some column
            output = output[
                ~output["name"].isin(
                    [
                        "AA_PROFILE",
                        "AA_X_PROFILE",
                        "NUC_N_PROFILE",
                        "NUC_PROFILE",
                        "IMPORTED",
                        "MODIFIED",
                    ]
                )
            ]
        return output
