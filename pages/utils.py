import re
from re import finditer

import pandas as pd

from pages.DBManager import DBManager

# from matplotlib.colors import to_rgba


def getRGBfromI(RGBint):
    blue = RGBint & 255
    green = (RGBint >> 8) & 255
    red = (RGBint >> 16) & 255
    return red, green, blue


def get_colour_map_gene(reference):
    """
    Input: Reference accession.
    Output: the dataframe contain unique colour mapping with gene of given REF.
    """
    with DBManager() as dbm:
        list_dict = dbm.get_reference_gene(reference)

    df = pd.DataFrame(list_dict)
    # * Unroll arguments from tuple
    df["color_hex"] = df.apply(
        lambda row: "#{:02x}{:02x}{:02x}".format(*getRGBfromI(row["element.start"])),
        axis=1,
    )
    # df.to_csv("text.tsv", sep="\t")
    return df


# Hard code !!
# FIXME: preload every reference/ build all DF for all references.
NC063_df = get_colour_map_gene("NC_063383.1")
ON563_df = get_colour_map_gene("ON563414.3")
MT903_df = get_colour_map_gene("MT903344.1")
# and save it into dict {"MT903344.1": df , "NC_063383.1"; df ... }
all_ref_dict = {
    "NC_063383.1": get_colour_map_gene("NC_063383.1"),
    "MT903344.1": get_colour_map_gene("MT903344.1"),
    "ON563414.3": get_colour_map_gene("ON563414.3"),
}


def get_gene_byNT(reference, mutation="del:136552-136554"):
    """
    Map the given NT mutation with the given reference to
    return the gene at CDS region.
    INPUT:
        del:136552-136554, G21723A, G52894AA

    RETURN:

        [{'reference.accession': 'NC_063383.1',
        'element.type': 'cds',
        'element.symbol': 'OPG153',
        'element.description': 'Orthopoxvirus A26L/A30L protein',
        'element.start': 136137,
        'element.end': 137667,  <--
        'element.strand': -1,
        'element.sequence': 'MANIINLWNGIVPMVQDVNVASITAFKSMIDETWDKKIEANT
        ILNTLDHNLNSIGHYCCDTVAVDRLEHHIETLGQYTVILARKINMQTLLFPWPLPTVHQHAID
        GSIPPHGRSTIL',
        'color_hex': '#0213c9'}]

    NOTE:
    1. Return as the list of dict.
    2. The return position  is NT position , however, it
    also return AA seq. which we can calculate AA position
    from the seq.

    """
    _df = all_ref_dict[reference]
    del_regex = re.compile(r"^(|[^:]+:)?([^:]+:)?del:(=?[0-9]+)(|-=?[0-9]+)?$")
    snv_regex = re.compile(r"^(|[^:]+:)?([^:]+:)?([A-Z]+)([0-9]+)(=?[A-Zxn]+)$")
    if match := snv_regex.match(mutation):
        # snv or insertion
        postions = [int(m.group(0)) for m in finditer(r"\d+", match[0])]

        result_dict = _df.query(
            f' `element.type` == "cds" & (`element.start` <= {postions[0]} & `element.end` >= {postions[0]})'
        ).to_dict("records")
    elif match := del_regex.match(mutation):
        # deletion
        postions = [int(m.group(0)) for m in finditer(r"\d+", match[0])]
        if len(postions) == 2:  # del:136552-136554
            QUERY_cmd = f' `element.type` == "cds" & (`element.start` <= {postions[0]} & `element.end` >= {postions[1]})'
        elif len(postions) == 1:  # del:25822
            QUERY_cmd = f' `element.type` == "cds" & (`element.start` <= {postions[0]} & `element.end` >= {postions[0]})'
        result_dict = _df.query(QUERY_cmd).to_dict("records")
    else:
        # not support
        raise
    # print(result_dict)
    return result_dict
