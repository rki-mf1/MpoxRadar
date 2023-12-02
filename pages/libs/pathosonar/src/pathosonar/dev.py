from Bio.Align.Applications import MafftCommandline
from tqdm import tqdm

from .dbm import sonarDBManager
from .logging import LoggingConfigurator
from .utils import calculate_mutation_type_DNA

# Initialize logger
LOGGER = LoggingConfigurator.get_logger()


def fix_annotation(db, debug):
    # get all variant
    with sonarDBManager(db, debug=debug, readonly=False) as dbm:
        all_variants = dbm.get_all_NT_variants()
        for each_variant in all_variants:
            _type = calculate_mutation_type_DNA(
                each_variant["ref"], each_variant["alt"]
            )
            dbm.update_variant_var_type(each_variant["id"], _type)

    # calculate


def fix_pre_ref(db, debug):
    with sonarDBManager(db, debug=debug, readonly=False) as dbm:

        # convert to dict
        ref_dict = dbm.sequence_references
        # get all variants.
        for each_variant in tqdm(dbm.get_all_NT_variants()):

            selected_ref_seq = ref_dict[each_variant["elem_ID"]]
            # ref_df.loc[ref_df['id'] == each_variant["elem_ID"]]["sequence"].values[0]
            # print(selected_ref_seq[10])
            # it was already 0-based position, so to get the before postion (-1)
            try:
                if each_variant["start"] - 1 < 0:
                    before_char = ""
                else:
                    before_char = selected_ref_seq[each_variant["start"] - 1]
            except Exception as e:
                LOGGER.error(e)
                raise
            dbm.update_elementID_variantTable(each_variant["id"], before_char)


def fix_element_id_NT(db, debug):
    with sonarDBManager(db, debug=debug, readonly=False) as dbm:
        for each_variant in tqdm(dbm.get_map_element_NT()):
            new_id = each_variant["element.id"]
            variant_id = each_variant["variant_id"]
            dbm.update_table_column(
                table_name="variant",
                column_name="element_id",
                new_value=new_id,
                condition_column="id",
                condition_value=variant_id,
            )


def test_align_mafft():
    LOGGER.info("Bye-bye Darling")
    mafft_exe = "mafft"
    mafft_cline = MafftCommandline(
        mafft_exe, input="/mnt/c/works/mafft/OQ331005.1.partial.fasta", auto=True
    )
    print(mafft_cline)
    stdout, stderr = mafft_cline()

    # find the fist position of '\n' to get seq1
    s1 = stdout.find("\n") + 1
    # find the start of second sequence position
    e = stdout[1:].find(">") + 1
    # find the '\n' of the second sequence to get seq2
    s2 = stdout[e:].find("\n") + e
    qry = stdout[s1:e].replace("\n", "").upper()
    ref = stdout[s2:].replace("\n", "").upper()
    return qry, ref
