import logging
import os, requests
import time
import pandas as pd
from attr import dataclass

from data_management.data_fetcher import DataFetcher, MutationFrequency
from util.Util import generate_96_mutation_types, getRGBfromI


@dataclass
class DjangoAPI(DataFetcher):
    # TODO-smc: replace with env var
    url: str = "http://127.0.0.1:8000/"
    usr: str = "root"
    pwd: str | None = os.environ.get("MPOX_PASSWORD")

    def _get_request(self, url, params=None):
        if self.pwd is None:
            raise ValueError("Password not set")
        response = requests.get(url, params=params, auth=(self.usr, self.pwd))
        if response.status_code != 200:
            logging.error(f"Error connecting to Django API: {response.text}")
            return {}
        return response

    def get_property_dates(self) -> dict[str, list[str]]:
        url = self.url + "properties/unique_collection_dates/"
        response = self._get_request(url)
        return response.json()

    def get_distinct_symbols(self) -> list[str]:
        return []

    def get_start_reference_id(self) -> int:
        return 0

    def get_reference_options(
        self,
    ):
        return []

    def get_sq_tech_options(
        self,
    ):
        return []

    def get_distinct_genes(
        self,
        filters={},
    ) -> dict[str, list[str]]:
        url = self.url + "elements/distinct_genes/"
        response = self._get_request(url, params=filters)
        return response.json()

    def get_distinct_countries(
        self,
    ):
        return []

    def get_variants_view_filtered(self, filters):
        return []

    def get_genes(self, filters) -> list[tuple]:
        url = self.url + "genes/"
        response = self._get_request(url, params=filters)
        return response.json()["results"]

    def get_raw_snp_1(self):
        url = self.url + "snp1/"
        response = self._get_request(url)
        return response.json()["results"]

    def get_mutation_signature(self, filters=None):
        url = self.url + "mutation_signature/"
        response = self._get_request(url, params=filters)
        return response.json()["results"]

    def count_unique_NT_Mut_Ref(self, filters=None):
        url = self.url + "samples/count_unique_nt_mut_ref_view_set/"
        response = self._get_request(url, params=filters)
        return response.json()

    def get_raw_mutation_signature(self, filters=None):
        url = self.url + "mutation_signature/raw/"
        response = self._get_request(url, params=filters)
        return response.json()["results"]

    def get_references(self):
        url = self.url + "elements/references/"
        response = self._get_request(url)
        return response.json()

    def get_mutation_frequency(self, query={}):
        url = self.url + "aa_mutations/mutation_frequency/"
        response = self._get_request(url, params=query)
        print(query)
        print(response.json())
        return [
            MutationFrequency(
                count=f["count"], variant=f["variant"], symbol=f["symbol"]
            )
            for f in response.json()
        ]

    # implement:
    def get_all_unique_samples(self):
        return []
        url = self.url + "samples/"
        response = self._get_request(url)
        return response.json()

    def get_all_seqtech(self, filters={}) -> dict:
        url = self.url + "properties/unique_sequencing_techs/"
        response = self._get_request(url, params=filters)
        return response.json()

    def get_high_mutation(self):
        return []
        url = self.url + "high_mutation/"
        response = self._get_request(url)
        return response.json()

    def get_newest_samples(self):
        return []
        url = self.url + "newlyadded_sample/"
        response = self._get_request(url)
        return response.json()

    def get_all_country(self, filters={}) -> dict[str, list[str]]:
        url = self.url + "properties/unique_countries/"
        response = self._get_request(url, params=filters)
        return response.json()

    def get_top3_country(self):
        return []
        url = self.url + "top3_country/"
        response = self._get_request(url)
        return response.json()

    def count_unique_mut_ref(self):
        return []
        url = self.url + "count_unique_mut_ref/"
        response = self._get_request(url)
        return response.json()

    # //

    def calculate_tri_mutation_sig(self):  # noqa: C901
        """
        List all 96 possible mutation types
        (e.g. A[C>A]A, A[C>A]T, etc.).
        """
        # TODO-smc make calculations in backend, specify endpoint for this (!!! keine alt = N mutationen)

        start = time.time()

        data_ = self.get_raw_mutation_signature()
        total_mutations = self.count_unique_NT_Mut_Ref()
        all_references_dict = {
            x.get("accession"): x.get("sequence") for x in self.get_references()
        }

        final_dict = {}
        # calculate freq.
        for mutation in data_:
            accession = mutation.get("reference_accession")

            if accession not in final_dict:
                final_dict[accession] = generate_96_mutation_types()

            ref = mutation.get("ref")
            alt = mutation.get("alt")
            mutation_pos_before = mutation.get("start") - 1
            mutation_pos_after = mutation.get("end")

            # get NT from position.
            ref_seq = all_references_dict[accession]
            nt_before = None
            nt_after = None
            try:
                nt_before = ref_seq[mutation_pos_before]
                nt_after = ref_seq[mutation_pos_after]
            except IndexError:
                logging.error("IndexError")
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

    def calculate_mutation_sig(self):
        """
        Calculate the
        six classes of base substitution: C>A, C>G, C>T, T>A, T>C, T>G.
        """
        # TODO-smc make calculations in backend, specify endpoint for this
        start = time.time()

        data_ = self.get_mutation_signature()
        total_mutations = self.count_unique_NT_Mut_Ref()

        # Define a dictionary to store the mutation counts for each reference accession
        mutation_counts = {}

        # Loop through the mutation data and increment the appropriate mutation count
        for mutation in data_:
            # temporarily changed to django object reference
            accession = mutation.get("reference_accession")
            ref = mutation.get("ref")
            alt = mutation.get("alt")
            mutation_type = f"{ref}>{alt}"

            if accession not in mutation_counts:
                mutation_counts[accession] = {}
            if mutation_type not in mutation_counts[accession]:
                mutation_counts[accession][mutation_type] = 0

            mutation_counts[accession][mutation_type] += mutation["count"]

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

    def create_snp_table(self):  # noqa: C901
        start = time.time()

        data_ = self.get_variants_view_filtered({})
        all_references_dict = {}

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
                logging.warning("IndexError")
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
                # logging.warning("IndexError")
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

    def get_colour_map_gene(self, reference):
        """
        Input: Reference accession.
        Output: the dataframe contain unique colour mapping with gene of given REF.
        """
        list_dict = self.get_genes(
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
