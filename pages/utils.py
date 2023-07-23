import bz2
from datetime import datetime
from datetime import timedelta
import os
import re
from re import finditer

import _pickle as cPickle
import pandas as pd
import plotly.express as px
from data_management.api.django.django_api import DjangoAPI

from data_management.api.mariadb_direct.db_manager import DBManager

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
    # with DBManager() as dbm:
    #        list_dict = dbm.get_reference_gene(reference)
    list_dict = DjangoAPI.get_instance().get_genes(
        {
            "reference__accession": reference,
            "element__type": "cds",
        }
    )
    df = pd.DataFrame(list_dict)
    # * Unroll arguments from tuple
    df["color_hex"] = df.apply(
        lambda row: "#{:02x}{:02x}{:02x}".format(*getRGBfromI(row["start"])),
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


def get_color_dict(api: DjangoAPI):
    """
    defined color by mutation
    color scheme contains 24 different colors, if #mutations>24 use second color scheme with 24 colors
    more mutations --> color schema starts again (max 48 different colors)
    wildtype= green, no_mutation (no sequence meets the user selected mutations, dates, location) = grey
    """
    color_dict = {}
    color_schemes = px.colors.qualitative.Dark24
    genes = api.get_distinct_symbols()
    for i, gene in enumerate(genes):
        j = i % 24
        color_dict[gene] = color_schemes[j]
    color_dict["no_gene"] = "grey"
    color_dict["unchanged"] = "grey"
    return color_dict


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


# Pickle a file and then compress it into a file with extension
def compressed_pickle(title, data):
    with bz2.BZ2File(title, "w") as f:
        cPickle.dump(data, f)


# Load any compressed pickle file
def decompress_pickle(file):
    data = bz2.BZ2File(file, "rb")
    data = cPickle.load(data)
    return data


def is_file_older_than(file, delta=timedelta(days=1)):
    cutoff = datetime.utcnow() - delta
    mtime = datetime.utcfromtimestamp(os.path.getmtime(file))
    if mtime < cutoff:
        return True
    return False


def write_Cpickle(filename, data):
    with open(filename, "wb") as output_file:
        cPickle.dump(data, output_file)


def load_Cpickle(filename):
    with open(filename, "rb") as input_file:
        data = cPickle.load(input_file)
    return data


def generate_96_mutation_types():
    mutation_types = {}
    substitution_classes = ["C>A", "C>G", "C>T", "T>A", "T>C", "T>G"]
    possible_nucleotides = ["A", "C", "G", "T"]
    for n1 in substitution_classes:
        if n1 not in mutation_types:
            mutation_types[n1] = {}
        for start in possible_nucleotides:
            for end in possible_nucleotides:
                mutation_type = start + n1 + end
                mutation_types[n1][mutation_type] = 0
    return mutation_types
