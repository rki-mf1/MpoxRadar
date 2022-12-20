#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# DEPENDENCIES
import sys
from textwrap import fill

import pandas as pd

from .config import DB_URL
from .DBManager import DBManager
from .libs.mpxsonar.src.mpxsonar.basics import sonarBasics
from .libs.mpxsonar.src.mpxsonar.dbm import sonarDBManager


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


def get_freq_mutation(args):
    with sonarDBManager(args.db, readonly=False) as dbm:
        cursor = dbm.our_match()
        df = pd.DataFrame(cursor)
        print(df)


def match_controller(args):  # noqa: C901
    props = {}
    reserved_props = {}

    with sonarDBManager(args.db, readonly=False, debug=args.debug) as dbm:
        if args.reference:
            if len(dbm.references) != 0 and args.reference not in [
                d["accession"] for d in dbm.references
            ]:
                return f"{args.reference} reference is not available."
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


def get_all_references():
    _list = []
    with DBManager() as dbm:
        list_dict = dbm.references
        for _dict in list_dict:
            # print(_dict)
            if _dict["accession"] in ["NC_063383.1", "MT903344.1", "ON563414.3"]:
                _list.append({"value": _dict["accession"], "label": _dict["accession"]})
    # logging_radar.info(_dict)
    return _list


def get_all_seqtech():
    _list = []
    with DBManager() as dbm:
        list_dict = dbm.get_all_SeqTech()
        for _dict in list_dict:
            # print(_dict)
            if _dict["value_text"] == "":
                _list.append({"value": _dict["value_text"], "label": "n/a"})
            else:
                _list.append(
                    {"value": _dict["value_text"], "label": _dict["value_text"]}
                )
    # logging_radar.info(_dict)
    return _list


def get_value_by_reference(checked_ref):
    output_df = pd.DataFrame()
    for ref in checked_ref:
        print("Query " + ref)
        _df = sonarBasicsChild.match(DB_URL, reference=ref)
        if type(_df) == str:
            continue
        output_df = pd.concat([output_df, _df], ignore_index=True)
    return output_df


def get_value_by_filter(checked_ref, mut_checklist, seqtech_checklist):
    output_df = pd.DataFrame()
    
    if len(checked_ref) == 0:  # all hardcode for now TODO:
        checked_ref = ["NC_063383.1", "MT903344.1", "ON563414.3"]

    propdict = {}
    if seqtech_checklist:
        propdict["SEQ_TECH"] = seqtech_checklist
    print("SEQ_TECH:" + str(propdict))
    
    mut_profiles = []
    if mut_checklist:
        mut_profiles.append(mut_checklist)

    print(mut_profiles)

    for ref in checked_ref:
        print("Query " + ref)
        _df = sonarBasicsChild.match(DB_URL, profiles=mut_profiles, reference=ref, propdict=propdict)
        if type(_df) == str:
            continue
        output_df = pd.concat([output_df, _df], ignore_index=True)
    return output_df


def get_high_mutation():
    _list = []
    with DBManager() as dbm:
        list_dict = dbm.get_high_mutation()
        for _dict in list_dict:
            # print(_dict)

            _list.append({"value": _dict["variant.label"], "label": _dict["variant.label"]})
    # logging_radar.info(_dict)
    return _list