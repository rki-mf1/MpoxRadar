from dash import html
import pandas as pd

# from tabulate import tabulate


def get_all_frequency_sorted_seqtech(propertyView):
    df_grouped_by_seqtech = (
        propertyView[["sample.id", "SEQ_TECH"]]
        .groupby(["SEQ_TECH"])
        .count()
        .reset_index()
        .sort_values(["sample.id"], ascending=False)
    )
    sorted_seqtech = df_grouped_by_seqtech["SEQ_TECH"].tolist()
    sorted_seqtech = [
        "not defined" if seqtech == "" else seqtech for seqtech in sorted_seqtech
    ]
    sorted_seqtech_dict = [
        {"label": seqtech, "value": seqtech, "disabled": False}
        for seqtech in sorted_seqtech
    ]
    return sorted_seqtech_dict


def get_all_frequency_sorted_mutation(df_worldMap, reference_id, color_dict):
    df = df_worldMap[(df_worldMap["reference.id"] == int(reference_id))][
        ["variant.label", "element.symbol", "number_sequences"]
    ]
    df_grouped_by_mutation = (
        df.groupby(["variant.label", "element.symbol"]).sum().reset_index()
    )
    df_grouped_by_mutation = df_grouped_by_mutation.sort_values(
        ["number_sequences"], ascending=False
    )
    sorted_mutations_dict = [
        {
            "label": html.Span(gene_mut[1], style={"color": color_dict[gene_mut[0]]}),
            "value": gene_mut[1],
        }
        for gene_mut in list(
            zip(
                df_grouped_by_mutation["element.symbol"],
                df_grouped_by_mutation["variant.label"],
            )
        )
    ]
    return sorted_mutations_dict


# TODO check when reference.accession = NA, ""
def get_all_references(variantView):
    references = (
        variantView[["reference.accession", "reference.id"]]
        .dropna()
        .drop_duplicates()
        .values.tolist()
    )
    references.sort(key=lambda x: x[1])
    references = [{"label": x[0], "value": x[1], "disabled": False} for x in references]
    return references


def get_all_frequency_sorted_countries(propertyView):
    df_grouped_by_country = (
        propertyView[["sample.id", "COUNTRY"]]
        .groupby(["COUNTRY"])
        .count()
        .reset_index()
        .sort_values(["sample.id"], ascending=False)
    )
    sorted_countries = df_grouped_by_country["COUNTRY"].tolist()
    sorted_country_dict = [
        {"label": mut, "value": mut, "disabled": False} for mut in sorted_countries
    ]
    return sorted_country_dict


def get_all_genes_per_reference(variantView, reference_id, color_dict):
    df = variantView[
        (variantView["reference.id"] == reference_id)
        & (variantView["element.type"] == "cds")
    ]
    gene_list = list(df["element.symbol"].unique())
    gene_dict = [
        {"label": html.Span(gene, style={"color": color_dict[gene]}), "value": gene}
        for gene in gene_list
    ]
    return gene_dict


def get_frequency_sorted_mutation_by_filters(
    variantView_mut_ref_select, propertyView_seq_tech, color_dict
):
    df_merge = pd.merge(
        variantView_mut_ref_select, propertyView_seq_tech, how="inner", on="sample.id"
    )[["sample.id", "variant.label", "element.symbol"]]
    df_grouped_by_mutation = (
        df_merge.groupby(["variant.label", "element.symbol"])
        .count()
        .reset_index()
        .sort_values(["sample.id"], ascending=False)
    )
    sorted_mutations_dict = [
        {
            "label": html.Span(gene_mut[1], style={"color": color_dict[gene_mut[0]]}),
            "value": gene_mut[1],
        }
        for gene_mut in list(
            zip(
                df_grouped_by_mutation["element.symbol"],
                df_grouped_by_mutation["variant.label"],
            )
        )
    ]
    return sorted_mutations_dict


def get_frequency_sorted_mutation_by_df(df, color_dict):
    df = (
        df.groupby(df.columns.tolist())
        .size()
        .reset_index()
        .rename(columns={0: "count"})
    )
    df_grouped_by_mutation = df.sort_values(["count"], ascending=False)
    sorted_mutations_dict = [
        {
            "label": html.Span(gene_mut[1], style={"color": color_dict[gene_mut[0]]}),
            "value": gene_mut[1],
        }
        for gene_mut in list(
            zip(
                df_grouped_by_mutation["element.symbol"],
                df_grouped_by_mutation["variant.label"],
            )
        )
    ]
    return sorted_mutations_dict


def get_mutations_by_filters(variantView_mut_ref_select, propertyView_seq_tech):
    df_merge = pd.merge(
        variantView_mut_ref_select, propertyView_seq_tech, how="inner", on="sample.id"
    )[["sample.id", "variant.label", "element.symbol"]]
    return df_merge


def get_all_frequency_sorted_countries_by_filters(df_prop, country_options):
    df_grouped_by_country = (
        df_prop.groupby(["COUNTRY"])
        .count()
        .reset_index()
        .sort_values(["sample.id"], ascending=False)
    )
    sorted_countries = df_grouped_by_country["COUNTRY"].tolist()
    not_in_list = [
        c["value"] for c in country_options if c["value"] not in sorted_countries
    ]
    sorted_country_dict = [
        {"label": c, "value": c, "disabled": False} for c in sorted_countries
    ]
    sorted_country_dict.extend(
        [{"label": c, "value": c, "disabled": True} for c in not_in_list]
    )
    return sorted_country_dict


def get_frequency_sorted_seq_techs_by_filters(
    df_mut_ref_select, propertyView, tech_options
):
    df = pd.merge(df_mut_ref_select, propertyView, how="inner", on="sample.id")
    df_grouped_by_seq_tech = (
        df[["sample.id", "SEQ_TECH"]]
        .groupby(["SEQ_TECH"])
        .count()
        .reset_index()
        .sort_values(["sample.id"], ascending=False)
    )
    sorted_seq_tech_list = df_grouped_by_seq_tech["SEQ_TECH"].tolist()
    not_in_list = [
        tech["value"]
        for tech in tech_options
        if tech["value"] not in sorted_seq_tech_list
    ]
    sorted_seq_tech_dict = [
        {"label": seqtech, "value": seqtech, "disabled": False}
        for seqtech in sorted_seq_tech_list
    ]
    sorted_seq_tech_dict.extend(
        [
            {"label": seqtech, "value": seqtech, "disabled": True}
            for seqtech in not_in_list
        ]
    )
    return sorted_seq_tech_dict
