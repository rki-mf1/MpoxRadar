import pandas as pd

from pages.DBManager import DBManager

# from matplotlib.colors import to_rgba


def getRGBfromI(RGBint):
    blue = RGBint & 255
    green = (RGBint >> 8) & 255
    red = (RGBint >> 16) & 255
    return red, green, blue


def get_colour_map_gene(reference):

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
