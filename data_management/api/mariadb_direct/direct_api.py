import logging
import time
from data_management.api.mariadb_direct.db_manager import DBManager
from data_management.data_fetcher import DataFetcher
import pandas as pd

from util.Util import generate_96_mutation_types, getRGBfromI

class DirectAPI(DataFetcher):
    def get_all_unique_samples(self):
        total = 0
        with DBManager() as dbm:
            total = dbm.count_all_samples()
        return total

    def get_newest_samples(self):
        total = 0
        with DBManager() as dbm:
            total = dbm.count_lastAdded30D_sample()
        return total

    def get_all_country(self):
        total = 0
        with DBManager() as dbm:
            total = dbm.count_all_country()
        return total

    def get_top3_country(self):
        """
        top 3 contries that have most samples
        """
        return_string = " "
        with DBManager() as dbm:
            list_dict = dbm.count_top3_country()
        return_string = ", ".join(_dict["value_text"] for _dict in list_dict)
        return return_string

    def count_unique_mut_ref(self):
        """
        "Number of mutations", i.e., min and max of number of unique mutations
        (compared to each reference genome).
        """
        return_string = (
            "0 - 0 (cannot compute MIN/MAX, due to number of reference is less than 2)"
        )
        with DBManager() as dbm:
            list_dict = dbm.count_unique_mut_ref()
        if len(list_dict) < 2:
            return return_string
        # it was already sorted.
        # get first
        first_dict = list_dict[0]
        # get last
        last_dict = list_dict[-1]
        return_string = f"{last_dict['max_each_ref']} - {first_dict['max_each_ref']}"
        return return_string

    def calculate_tri_mutation_sig(self):  # noqa: C901
        """
        List all 96 possible mutation types
        (e.g. A[C>A]A, A[C>A]T, etc.).
        """
        # TODO-smc make calculations in backend, specify endpoint for this
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
                # redis_manager.set("data_tri_mutation_sig", json.dumps(data_), ex=3600 * 23)
                # redis_manager.set(
                #    "total_tri_mutation_sig", json.dumps(total_), ex=3600 * 23
                # )
            # normalize the total number of mutations for each reference accession
            total_mutations = {x["reference.accession"]: x["Freq"] for x in total_}

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
                redis_manager.set(
                    "data_mutation_sig", json.dumps(data_), ex=3600 * 23
                )
                redis_manager.set(
                    "total_mutation_sig", json.dumps(total_), ex=3600 * 23
                )

        # normalize the total number of mutations for each reference accession
        total_mutations = {x["reference.accession"]: x["Freq"] for x in total_}

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

        if os.environ.get("REST_IMPLEMENTATION") == "True":
            data_ = DjangoAPI.get_instance().get_variants_view_filtered({})
            all_references_dict = {}

        elif redis_manager and redis_manager.exists("data_snp_table"):
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
                # redis_manager.set("data_snp_table", json.dumps(data_), ex=3600 * 23)

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

    def get_all_seqtech(self):
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
        # logging.info(_dict)
        return _list

    def get_all_references(self):
        _list = []
        with DBManager() as dbm:
            list_dict = dbm.references
            for _dict in list_dict:
                # print(_dict)
                if _dict["accession"] in ["NC_063383.1", "MT903344.1", "ON563414.3"]:
                    _list.append(
                        {"value": _dict["accession"], "label": _dict["accession"]}
                    )
        # logging.info(_dict)
        return _list

    def get_high_mutation(self):
        _list = []
        with DBManager() as dbm:
            list_dict = dbm.get_high_mutation()
            for _dict in list_dict:
                # print(_dict)

                _list.append(
                    {"value": _dict["variant.label"], "label": _dict["variant.label"]}
                )
        # logging.info(_dict)
        return _list

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
            lambda row: "#{:02x}{:02x}{:02x}".format(*getRGBfromI(row["start"])),
            axis=1,
        )
        # df.to_csv("text.tsv", sep="\t")
        return df