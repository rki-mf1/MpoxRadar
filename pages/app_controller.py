#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# DEPENDENCIES
import json
import sys
from textwrap import fill
import time

import pandas as pd

from pages.config import DB_URL
from pages.config import logging_radar
from pages.config import redis_manager
from pages.DBManager import DBManager
from pages.utils import generate_96_mutation_types
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
    # print(props)
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

    if (
        len(checked_ref) == 0
    ):  # all hardcode for now TODO: remove the hardcode if possible.
        checked_ref = ["NC_063383.1", "MT903344.1", "ON563414.3"]

    propdict = {}
    if seqtech_checklist:
        propdict["SEQ_TECH"] = seqtech_checklist
    # print("SEQ_TECH:" + str(propdict))

    mut_profiles = []
    if mut_checklist:
        mut_profiles.append(mut_checklist)

    # print(mut_profiles)

    mut_profiles = []
    if mut_checklist:
        mut_profiles.append(mut_checklist)

    # print(mut_profiles)

    for ref in checked_ref:
        print("Query " + ref)
        _df = sonarBasicsChild.match(
            DB_URL, profiles=mut_profiles, reference=ref, propdict=propdict
        )
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

            _list.append(
                {"value": _dict["variant.label"], "label": _dict["variant.label"]}
            )
    # logging_radar.info(_dict)
    return _list


# ----- descriptive summary part


def get_all_unique_sample():
    total = 0
    with DBManager() as dbm:
        total = dbm.count_all_samples()
    return total


def get_newlyadded_sample():
    total = 0
    with DBManager() as dbm:
        total = dbm.count_lastAdded30D_sample()
    return total


def get_all_country():
    total = 0
    with DBManager() as dbm:
        total = dbm.count_all_country()
    return total


def get_top3_country():
    """
    top 3 contries that have most samples
    """
    return_string = " "
    with DBManager() as dbm:
        list_dict = dbm.count_top3_country()
    return_string = ", ".join(_dict["value_text"] for _dict in list_dict)
    return return_string


def count_unique_MutRef():
    """
    "Number of mutations", i.e., min and max of number of unique mutations
    (compared to each reference genome).
    """
    return_string = (
        "0 - 0 (cannot compute MIN/MAX, due to number of reference is less than 2)"
    )
    with DBManager() as dbm:
        list_dict = dbm.count_unique_MutRef()
    if len(list_dict) < 2:
        return return_string
    # it was already sorted.
    # get first
    first_dict = list_dict[0]
    # get last
    last_dict = list_dict[-1]
    return_string = f"{last_dict['max_each_ref']} - {first_dict['max_each_ref']}"
    return return_string


def calculate_tri_mutation_sig():  # noqa: C901
    """
    List all 96 possible mutation types
    (e.g. A[C>A]A, A[C>A]T, etc.).
    """
    start = time.time()

    if (
        redis_manager
        and redis_manager.exists("data_tri_mutation_sig")
        and redis_manager.exists("total_tri_mutation_sig")
    ):
        data_ = json.loads(redis_manager.get("data_tri_mutation_sig"))
        total_ = json.loads(redis_manager.get("total_tri_mutation_sig"))
        with DBManager() as dbm:
            all_references_dict = {
                x["accession"]: x["sequence"] for x in dbm.references
            }
    else:
        with DBManager() as dbm:
            data_ = dbm.get_raw_mutation_signature()
            total_ = dbm.count_unique_NT_Mut_Ref()
            all_references_dict = {
                x["accession"]: x["sequence"] for x in dbm.references
            }
            # Convert the list to a JSON string
            redis_manager.set("data_tri_mutation_sig", json.dumps(data_), ex=3600 * 23)
            redis_manager.set(
                "total_tri_mutation_sig", json.dumps(total_), ex=3600 * 23
            )

    final_dict = {}
    # calculate freq.
    for mutation in data_:
        accession = mutation["reference.accession"]

        if accession not in final_dict:
            final_dict[accession] = generate_96_mutation_types()

        ref = mutation["variant.ref"]
        alt = mutation["variant.alt"]
        mutation_pos_before = mutation["variant.start"] - 1
        mutation_pos_after = mutation["variant.end"]

        # get NT from position.
        ref_seq = all_references_dict[accession]
        try:
            nt_before = ref_seq[mutation_pos_before]
            nt_after = ref_seq[mutation_pos_after]
        except IndexError:
            logging_radar.error("IndexError")
            print(mutation)
            print(
                "IndexError:",
                nt_before,
                mutation_pos_before,
                nt_after,
                mutation_pos_after,
            )
            print("---------")
            continue
        mutation_type = f"{ref}>{alt}"
        _type = f"{nt_before}{ref}>{alt}{nt_after}"

        try:
            final_dict[accession][mutation_type][_type] += 1
        except KeyError:
            print("mutation_type:", mutation_type)
            print("_type:", _type)
            print("final_dict ->", final_dict[accession][mutation_type][_type])
            raise
    # normalize the total number of mutations for each reference accession
    total_mutations = {x["reference.accession"]: x["Freq"] for x in total_}
    # Calculate the mutation signature for each reference accession

    for accession in final_dict:
        for mutation_type in final_dict[accession]:
            for _type in final_dict[accession][mutation_type]:
                count = final_dict[accession][mutation_type][_type]
                freq = round(count / total_mutations[accession], 6)
                final_dict[accession][mutation_type][_type] = freq
    # print(final_dict)
    end = time.time()
    print("calculate_tri_mutation_sig", round(end - start, 4))
    return final_dict


def calculate_mutation_sig():
    """
    Calculate the
    six classes of base substitution: C>A, C>G, C>T, T>A, T>C, T>G.
    """
    start = time.time()
    if (
        redis_manager
        and redis_manager.exists("data_mutation_sig")
        and redis_manager.exists("total_mutation_sig")
    ):
        data_ = json.loads(redis_manager.get("data_mutation_sig"))
        total_ = json.loads(redis_manager.get("total_mutation_sig"))
    else:
        with DBManager() as dbm:
            data_ = dbm.get_mutation_signature()
            total_ = dbm.count_unique_NT_Mut_Ref()
            # Convert the list to a JSON string
            redis_manager.set("data_mutation_sig", json.dumps(data_), ex=3600 * 23)
            redis_manager.set("total_mutation_sig", json.dumps(total_), ex=3600 * 23)

    # Define a dictionary to store the mutation counts for each reference accession
    mutation_counts = {}

    # Loop through the mutation data and increment the appropriate mutation count
    for mutation in data_:
        accession = mutation["reference.accession"]
        ref = mutation["variant.ref"]
        alt = mutation["variant.alt"]
        mutation_type = f"{ref}>{alt}"

        if accession not in mutation_counts:
            mutation_counts[accession] = {}
        if mutation_type not in mutation_counts[accession]:
            mutation_counts[accession][mutation_type] = 0

        mutation_counts[accession][mutation_type] += mutation["count"]

    # normalize the total number of mutations for each reference accession
    total_mutations = {x["reference.accession"]: x["Freq"] for x in total_}

    # Calculate the mutation signature for each reference accession
    mutation_signature = {}
    for accession in mutation_counts:
        signature = {}
        for mutation_type in mutation_counts[accession]:
            count = mutation_counts[accession][mutation_type]
            freq = round(count / total_mutations[accession], 4)
            signature[mutation_type] = freq
        mutation_signature[accession] = signature
    # print(mutation_signature)
    end = time.time()
    print("calculate_mutation_sig", round(end - start, 4))
    return mutation_signature


def create_snp_table():  # noqa: C901
    start = time.time()

    if redis_manager and redis_manager.exists("data_snp_table"):
        data_ = json.loads(redis_manager.get("data_snp_table"))

        with DBManager() as dbm:
            all_references_dict = {
                x["accession"]: x["sequence"] for x in dbm.references
            }
    else:
        with DBManager() as dbm:
            data_ = dbm.get_raw_snp_1()
            all_references_dict = {
                x["accession"]: x["sequence"] for x in dbm.references
            }
            # Convert the list to a JSON string
            redis_manager.set("data_snp_table", json.dumps(data_), ex=3600 * 23)

    final_dict = {}
    # calculate freq.
    for mutation in data_:
        accession = mutation["reference.accession"]
        ref_seq = all_references_dict[accession]

        if accession not in final_dict:
            final_dict[accession] = {}

        ref = mutation["variant.ref"]
        alt = mutation["variant.alt"]
        mutation_pos_before = mutation["variant.start"] - 1
        mutation_pos_after = mutation["variant.end"]

        # get NT from position.
        # FIXME: There will be a problem if the end position is out of bound.
        """
        for example,
        MPXRadar:2023-04-11 14:58:06 ERROR: IndexError
        {'reference.accession': 'NC_063383.1', 'variant.ref': 'T',
          'variant.alt': 'A', 'variant.start': 197208, 'variant.end': 197209}
        IndexError: A 197207 A 197209
        """
        try:
            nt_before = ref_seq[mutation_pos_before]

        except IndexError:
            logging_radar.warning("IndexError")
            print(mutation)
            print(
                "IndexError before:",
                nt_before,
                mutation_pos_before,
            )
            print("---------")
            nt_before = ""

        try:
            nt_after = ref_seq[mutation_pos_after]
        except IndexError:
            # logging_radar.warning("IndexError")
            # print(mutation)
            # print(
            #    "IndexError after:",
            #    nt_after,
            #    mutation_pos_after,
            # )
            # print("---------")
            nt_after = ""

        # single NT
        # C > T
        try:
            mutation_type = f"{ref}>{alt}"
            _type = f"{ref}>{alt}"

            if _type not in final_dict[accession]:
                final_dict[accession][_type] = 0

            final_dict[accession][_type] += 1
        except KeyError:
            print("mutation_type:", mutation_type)
            print("single NT: _type:", _type)
            print("final_dict ->", final_dict[accession][_type])
            raise

        # 2 NTs: End changes
        # GC > GT
        try:
            mutation_type = f"{ref}>{alt}"
            _type = f"{nt_before}{ref}>{nt_before}{alt}"

            if _type not in final_dict[accession]:
                final_dict[accession][_type] = 0

            final_dict[accession][_type] += 1
        except KeyError:
            print("mutation_type:", mutation_type)
            print("2 NTs: End changes:", _type)
            print("final_dict ->", final_dict[accession][_type])
            raise

        # 2 NTs: Begin changes
        # CA > TA
        try:
            mutation_type = f"{ref}>{alt}"
            _type = f"{ref}{nt_after}>{alt}{nt_after}"

            if _type not in final_dict[accession]:
                final_dict[accession][_type] = 0

            final_dict[accession][_type] += 1
        except KeyError:
            print("mutation_type:", mutation_type)
            print("2 NTs: Begin changes:", _type)
            print("final_dict ->", final_dict[accession][_type])
            raise

        # 3 NTs: middle changes
        # CA > TA
        try:
            mutation_type = f"{ref}>{alt}"
            _type = f"{nt_before}{ref}>{alt}{nt_after}"

            if _type not in final_dict[accession]:
                final_dict[accession][_type] = 0

            final_dict[accession][_type] += 1
        except KeyError:
            print("mutation_type:", mutation_type)
            print("3 NTs: Middle changes:", _type)
            print("final_dict ->", final_dict[accession][_type])
            raise

    # Convert the dictionary to a dataframe
    df = pd.DataFrame.from_dict(final_dict, orient="index")
    # Add a column for genome assembly
    df["genome_assembly"] = df.index
    # Reset the index and add a column for the mutation
    df = df.reset_index()
    df = pd.melt(
        df,
        id_vars=["index", "genome_assembly"],
        var_name="mutation",
        value_name="count",
    )
    df.drop(columns=["index"], inplace=True)
    end = time.time()
    print("create_snp_table", round(end - start, 4))
    return df
