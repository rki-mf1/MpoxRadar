from datetime import datetime
from dash import html
import pandas as pd


def select_variantView_dfs(df_dict, complete_partial_radio, reference_value, aa_nt_radio):
    variantView_dfs = [df_dict["variantView"]['complete'][reference_value][aa_nt_radio]]
    if complete_partial_radio == 'partial':
        variantView_dfs.append(df_dict["variantView"]['partial'][reference_value][aa_nt_radio])
    return variantView_dfs


def select_propertyView_dfs(df_dict, complete_partial_radio):
    propertyView_dfs = [df_dict["propertyView"]["complete"]]
    if complete_partial_radio == "partial":
        propertyView_dfs.append(df_dict["propertyView"]["partial"])
    return propertyView_dfs


def sort_and_extract_by_col(propertyView, col):
    df_grouped_by_col = (
        propertyView
            .groupby([col])
            .count()
            .reset_index()
            .sort_values(["sample.id"], ascending=False)
    )
    sorted_list = df_grouped_by_col[col].tolist()
    return sorted_list


# TODO error if difference between complete and partial
def get_all_references(df_dict):
    ref_ids = sorted(list(df_dict["variantView"]['complete'].keys()))
    ref_accs = [
        df_dict["variantView"]['complete'][ref]['cds'].iloc[0]['reference.accession']
        for ref in ref_ids
    ]
    references = [
        {"label": ref_acc, "value": ref_id, "disabled": False}
        for ref_acc, ref_id in zip(ref_accs, ref_ids)
    ]
    return references


def get_all_gene_dict(df_dict, reference_value, complete_partial_radio, color_dict):
    genes = set(
        df_dict['variantView']['complete'][reference_value]['cds']["element.symbol"]
    )
    if complete_partial_radio == 'partial':
        genes = genes.union(
            set(
                df_dict['variantView']['partial'][reference_value]['cds'][
                    "element.symbol"
                ]
            )
        )
    gene_list = sorted(list(genes))
    gene_dict = [
        {"label": html.Span(gene, style={"color": color_dict[gene]}), "value": gene}
        for gene in gene_list
    ]
    return gene_dict


def get_all_frequency_sorted_seqtech(df_dict):
    propertyView = pd.concat(
        [df_dict['propertyView']['complete'], df_dict['propertyView']['partial']],
        ignore_index=True,
        axis=0,
    )[["sample.id", "SEQ_TECH"]]
    sorted_seqtech = sort_and_extract_by_col(propertyView, "SEQ_TECH")

    # create seq tech options
    sorted_seqtech = [
        "not defined" if seqtech == "" else seqtech for seqtech in sorted_seqtech
    ]
    sorted_seqtech_dict = [
        {"label": seqtech, "value": seqtech, "disabled": False}
        for seqtech in sorted_seqtech
    ]
    return sorted_seqtech_dict


def get_all_frequency_sorted_countries_by_filters(
        df_dict,
        seqtech_value,
        complete_partial_radio,
        reference_value,
        gene_value,
        aa_nt='cds',
        min_date=None
):
    # complete samples, propertyView filtered by seqtech, gene, min date
    filtered_propertyView = filter_propertyView_by_seqtech_and_gene(
        df_dict['variantView']['complete'][reference_value][aa_nt],
        df_dict['propertyView']['complete'],
        seqtech_value,
        gene_value,
        aa_nt,
        min_date,
    )

    # add partial samples, propertyView filtered by seqtech, gene, min date
    if complete_partial_radio == 'partial':
        filtered_propertyView_partial = filter_propertyView_by_seqtech_and_gene(
            df_dict['variantView']['partial'][reference_value][aa_nt],
            df_dict['propertyView']['partial'],
            seqtech_value,
            gene_value,
            aa_nt,
            min_date,
        )
        filtered_propertyView = pd.concat(
            [filtered_propertyView, filtered_propertyView_partial],
            ignore_index=True,
            axis=0
        )
    # sort and extract filtered countries
    sorted_countries = sort_and_extract_by_col(filtered_propertyView, 'COUNTRY')
    country_options = [
        {"label": c, "value": c, "disabled": False} for c in sorted_countries
    ]
    return country_options


def filter_propertyView_by_seqtech_and_country(df, seqtech_value, country_value):
    return df[
        (df["SEQ_TECH"].isin(seqtech_value))
        & (df["COUNTRY"].isin(country_value))
        ]


def filter_propertyView_by_seqtech_and_gene(variantView, propertyView, seqtech_value, gene_value, aa_nt, min_date=None):
    if aa_nt == 'cds':
        sample_id_set = set(
            variantView[variantView["element.symbol"].isin(gene_value)]["sample.id"]
        )
    elif aa_nt == "source":
        sample_id_set = set(variantView["sample.id"])

    filtered_propertyView = propertyView[
        propertyView["SEQ_TECH"].isin(seqtech_value)
        & propertyView["sample.id"].isin(sample_id_set)]

    if min_date:
        filtered_propertyView = filtered_propertyView[
            (filtered_propertyView["COLLECTION_DATE"] >= datetime.strptime(min_date, "%Y-%m-%d").date())
        ]
    return filtered_propertyView


def filter_variantView_by_genes(df, gene_value):
    return df[df["element.symbol"].isin(gene_value)].reset_index(drop=True)


def filter_by_seqtech_country_gene_and_merge(propertyView, variantView, seqtech_value, country_value, gene_value):
    filtered_propertyView = filter_propertyView_by_seqtech_and_country(
        propertyView, seqtech_value, country_value
    )
    filtered_variantView = filter_variantView_by_genes(
        variantView, gene_value
    )
    merged_df = pd.merge(
        filtered_propertyView, filtered_variantView,
        how="inner",
        on="sample.id")[["sample.id", "variant.label", "gene:variant", "element.symbol"]]
    return merged_df


def get_frequency_sorted_cds_mutation_by_filters(
        df_dict,
        seqtech_value,
        country_value,
        gene_value,
        complete_partial_radio,
        reference_value,
        color_dict,
        min_nb_freq=1
):
    merged_df = filter_by_seqtech_country_gene_and_merge(
        df_dict["propertyView"]['complete'],
        df_dict['variantView']['complete'][reference_value]['cds'],
        seqtech_value,
        country_value,
        gene_value
    )

    if complete_partial_radio == 'partial':
        merged_df_2 = filter_by_seqtech_country_gene_and_merge(
            df_dict["propertyView"]['partial'],
            df_dict['variantView']['partial'][reference_value]['cds'],
            seqtech_value,
            country_value,
            gene_value
        )
        merged_df = pd.concat([merged_df, merged_df_2], ignore_index=True, axis=0)

    sorted_mutation_options, max_nb_freq, min_nb_freq = get_frequency_sorted_mutation_by_df(
        merged_df,
        color_dict,
        ["gene:variant", "element.symbol"],
        "cds",
        min_nb_freq
    )
    return sorted_mutation_options, max_nb_freq, min_nb_freq


def get_frequency_sorted_mutation_by_df(df, color_dict, variant_columns, mut_type, min_nb_freq=None):
    df = (
        df.groupby(variant_columns)
            .size()
            .reset_index()
            .rename(columns={0: "count"})
            .sort_values(["count"], ascending=False, ignore_index=True)
    )
    if not df.empty:
        max_freq_nb = df.iloc[0, -1]
        if min_nb_freq:
            if min_nb_freq > max_freq_nb:
                min_nb_freq = max_freq_nb
            if min_nb_freq == 0 and max_freq_nb > 0:
                min_nb_freq = 1
            df = df[df["count"] >= min_nb_freq]
    else:
        max_freq_nb = 0
    if mut_type == "cds":
        sorted_mutation_options = [
            {
                "label": html.Span(
                    gene_mut[1], style={"color": color_dict[gene_mut[0]]}
                ),
                "value": gene_mut[1],
                "freq": gene_mut[2],
            }
            for gene_mut in list(
                zip(
                    df["element.symbol"],
                    df["gene:variant"],
                    df["count"],
                )
            )
        ]
    else:
        sorted_mutation_options = [
            {"label": gene_mut[0], "value": gene_mut[0], "freq": gene_mut[1]}
            for gene_mut in list(
                zip(
                    df["variant.label"],
                    df["count"],
                )
            )
        ]

    return sorted_mutation_options, max_freq_nb, min_nb_freq


def get_sample_and_seqtech_df(variantView, propertyView, aa_nt_radio, gene_value, min_date=None):
    if aa_nt_radio == 'cds':
        variantView = variantView[variantView["element.symbol"].isin(gene_value)]
    if min_date:
        propertyView = propertyView[(propertyView['COLLECTION_DATE'] >=
                                     datetime.strptime(min_date, "%Y-%m-%d").date())]
    df = pd.merge(
        variantView, propertyView,
        how="inner",
        on="sample.id")[["sample.id", "SEQ_TECH"]]
    return df


def get_frequency_sorted_seq_techs_by_filters(
        df_dict,
        tech_options,
        complete_partial_radio,
        reference_value,
        gene_value,
        aa_nt_radio='cds',
        min_date=None
):
    df = get_sample_and_seqtech_df(
        df_dict['variantView']['complete'][reference_value][aa_nt_radio],
        df_dict["propertyView"]['complete'],
        aa_nt_radio,
        gene_value,
        min_date
    )

    if complete_partial_radio == 'partial':
        df2 = get_sample_and_seqtech_df(
            df_dict['variantView']['partial'][reference_value][aa_nt_radio],
            df_dict["propertyView"]['partial'],
            aa_nt_radio,
            gene_value,
            min_date
        )
        df = pd.concat([df, df2], ignore_index=True, axis=0)

    sorted_seq_tech_list = sort_and_extract_by_col(df, "SEQ_TECH")

    # create seq tech options, seq techs not in filters are shown as disabled
    not_in_list = [
        tech["value"]
        for tech in tech_options
        if tech["value"] not in sorted_seq_tech_list
    ]
    sorted_seq_tech_options = [
        {"label": seqtech, "value": seqtech, "disabled": False}
        for seqtech in sorted_seq_tech_list
    ]
    sorted_seq_tech_options.extend(
        [
            {"label": seqtech, "value": seqtech, "disabled": True}
            for seqtech in not_in_list
        ]
    )
    return sorted_seq_tech_options


def actualize_filters(
        df_dict,
        color_dict,
        triggered_id,
        aa_nt_radio,
        reference_value,
        select_all_seq_techs,
        select_all_genes,
        select_all_countries,
        complete_partial_radio,
        gene_options,
        country_options,
        seq_tech_options,
        gene_value,
        country_value,
        seq_tech_value,
        min_date=None
):
    if triggered_id.startswith("select_all_genes"):
        if len(select_all_genes) == 1:
            gene_value = [i["value"] for i in gene_options]
        elif len(select_all_genes) == 0:
            gene_value = []

    elif triggered_id.startswith("select_all_countries"):
        if len(select_all_countries) == 1:
            country_value = [i["value"] for i in country_options]
        elif len(select_all_countries) == 0:
            country_value = []

    elif triggered_id.startswith("select_all_seq_tech"):
        if len(select_all_seq_techs) == 1:
            seq_tech_value = [i["value"] for i in seq_tech_options]
        elif len(select_all_seq_techs) == 0:
            seq_tech_value = []

    # new gene option
    if triggered_id.startswith(
            ("complete_partial_radio", "aa_nt_radio", "reference_radio")
    ):
        if aa_nt_radio == "cds":
            gene_options = get_all_gene_dict(
                df_dict, reference_value, complete_partial_radio, color_dict
            )
            gene_value = [i["value"] for i in gene_options]
        elif aa_nt_radio == "source":
            gene_options = [{"value": 0, "label": "no_gene_options_for_nucleotides"}]
            gene_value = []

    # new seq tech option
    if triggered_id.startswith(
            (
                    "complete_partial_radio",
                    "aa_nt_radio",
                    "reference_radio",
                    "gene_dropdown",
                    "select_all_genes"
            )
    ):
        seq_tech_options = get_frequency_sorted_seq_techs_by_filters(
            df_dict,
            seq_tech_options,
            complete_partial_radio,
            reference_value,
            gene_value,
            aa_nt_radio,
            min_date,
        )
        seq_tech_value = [s["value"] for s in seq_tech_options]

    # new country option
    if triggered_id.startswith(
            (
                    "complete_partial_radio",
                    "aa_nt_radio",
                    "reference_radio",
                    "gene_dropdown",
                    "select_all_genes",
                    "select_all_seq_tech",
                    "seq_tech_dropdown"
            )
    ):
        country_options = get_all_frequency_sorted_countries_by_filters(
            df_dict,
            seq_tech_value,
            complete_partial_radio,
            reference_value,
            gene_value,
            aa_nt_radio,
            min_date,
        )
        country_value = [c["value"] for c in country_options]

    return (
        gene_options,
        gene_value,
        country_options,
        country_value,
        seq_tech_options,
        seq_tech_value,
    )
