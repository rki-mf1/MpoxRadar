#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# DEPENDENCIES

import sys
from textwrap import fill

import pandas as pd

from mpxsonar.basics import sonarBasics
from mpxsonar.dbm import sonarDBManager


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
        debug="False",
        showNX=False,
    ):
        """
        db = db connection
        profile

        """
        output = None
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
                if "IMPORTED" in df.columns and "MODIFIED" in df.columns:
                    df.drop(["IMPORTED", "MODIFIED"], axis=1, inplace=True)
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
                # TODO: remove this. and change
                sonarBasics.exportVCF(
                    cursor, reference=reference, outfile=outfile, na="*** no match ***"
                )
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
            # tmp fix.
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


def get_freq_mutation(args):
    with sonarDBManager(args.db, readonly=False) as dbm:
        cursor = dbm.our_match()
        df = pd.DataFrame(cursor)
        print(df)


def match_controller(args):  # noqa: C901
    props = {}
    reserved_props = {}

    with sonarDBManager(args.db, readonly=False, debug=args.debug) as dbm:
        for pname in dbm.properties:
            if hasattr(args, pname):
                props[pname] = getattr(args, pname)
        # check column output and property name
        if args.out_column != "all":
            out_column = args.out_column.strip()
            out_column_list = out_column.split(",")
            check = all(item in dbm.properties for item in out_column_list)
            if check:
                # sample.name is fixed
                valid_output_column = out_column_list + ["sample.name"]
            else:
                sys.exit(
                    "input error: "
                    + str(out_column_list)
                    + " one or more given name mismatch the available properties"
                )
        else:
            valid_output_column = "all"
    # for reserved keywords
    reserved_key = ["sample"]
    for pname in reserved_key:
        if hasattr(args, pname):
            if pname == "sample" and len(getattr(args, pname)) > 0:
                # reserved_props[pname] = set([x.strip() for x in args.sample])
                reserved_props = sonarBasics.set_key(
                    reserved_props, pname, getattr(args, pname)
                )
            # reserved_props[pname] = getattr(args, pname)
    format = "count" if args.count else args.format
    print(props)
    output = sonarBasicsChild.match(
        args.db,
        args.profile,
        reserved_props,
        props,
        outfile=args.out,
        output_column=valid_output_column,
        debug=args.debug,
        format=format,
        showNX=args.showNX,
        reference=args.reference,
    )
    return output
