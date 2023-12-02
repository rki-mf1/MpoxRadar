import collections
import csv
import json
import os
import sys
from typing import Any
from typing import Dict
from typing import Generator
from typing import Iterator
from typing import List
from typing import Optional
from typing import Set
from typing import Union

from Bio import SeqIO
from Bio.SeqFeature import CompoundLocation
from Bio.SeqFeature import FeatureLocation
from Bio.SeqFeature import SeqFeature
from Bio.SeqRecord import SeqRecord
from mpire import WorkerPool
import pandas as pd
from tqdm import tqdm

from .align import sonarAligner
from .annotation import read_sonar_hash
from .annotation import read_tsv_snpSift
from .basics import sonarBasics
from .cache import sonarCache
from .dbm import sonarDBManager
from .logging import LoggingConfigurator
from .utils_1 import get_filename_sonarhash

# Initialize logger
LOGGER = LoggingConfigurator.get_logger()


def print_max_min_rule(ref):
    up = int((len(ref) * 100.3) / 100)
    low = int((len(ref) * 99.7) / 100)
    return f"Accept lenght:{low}<{len(ref)}<{up}"


def check_seq_compact(ref, qry):
    qry_size = len(qry)
    up = int((len(ref) * 100.3) / 100)
    low = int((len(ref) * 99.7) / 100)
    if low < qry_size and qry_size < up:
        return True
    else:
        return False


def calculate_mutation_type_DNA(ref, alt):
    """
    example cases;
    1. C>T SNV
    2. T>TTT (insert two positions) frameshift
    3. TAG> deleltion
    4. A>AGGG insertion
    5. T> frameshift
    6. A>AGAAGTAGAA insertion
    7. >A frameshift
    # The
    Returns:
        str: The NT variant type. (SNV,DEL,INS,frameshift,unknown)
    """
    # to remove empty space from string ' '
    ref = ref.replace(" ", "")
    ref_len = len(ref)
    alt = alt.replace(" ", "")
    alt_len = len(alt)

    if ref_len == alt_len:
        return "SNV"
    elif ref_len != alt_len:  # INSERTION
        if ref_len < alt_len:

            if ref_len == 0:  # when the ref is empty
                if alt_len % 3 != 0:
                    return "frameshift"
                else:
                    return "INS"
            else:
                # need to ignore a first position at 'alt' before
                # doing a calucation.
                # (T>TTT, in this case TT will be counted only )
                alt_len = len(alt[1:])

                if alt_len % 3 != 0:
                    return "frameshift"
                else:
                    return "INS"

        elif ref_len > alt_len:  # DELETION
            if ref_len % 3 != 0:
                return "frameshift"
            else:
                return "DEL"
        else:
            return "unknown"
    else:
        return "unknown"


# CLASS
class sonarUtils:
    """
    A class used to perform operations on a Tool's database.
    """

    def __init__(self):
        pass

    # DATABASE HANDLING
    @staticmethod
    def setup_db(
        db_url: str,
        db_sql_script: Optional[str] = None,
        default_props: bool = False,
        reference_gb: Optional[str] = None,
        quiet: bool = False,
    ) -> None:
        """
        Set up database with provided configurations.

        Args:
            db_url (str): URL for the database.
            defaut_props (bool, optional): Flag to create pre-defined properties.
            reference_gb (str, optional): Reference GenBank file.
            quiet (bool, optional): Flag to suppress logging info.

        Raises:
            SystemExit: If the file already exists.
        """
        #  checking files
        if reference_gb and not os.path.isfile(reference_gb):
            LOGGER.error(f"The given genbank file {reference_gb} does not exist.")
            sys.exit(1)

        # creating database
        try:
            sonarDBManager.setup(db_url, db_sql_script=db_sql_script)

            with sonarDBManager(db_url, readonly=False, debug=quiet) as dbm:
                # adding build-in props
                sonarUtils._create_reserved_properties(dbm)

                # adding default props
                if default_props:
                    sonarUtils._create_predefined_properties(dbm)

                # adding reference
                if not reference_gb:
                    reference_gb = sonarUtils.get_default_reference_gb()
                records = [x for x in sonarUtils.iter_genbank(reference_gb)]
                sonarUtils._add_reference(dbm, records)

            if not quiet:
                LOGGER.info("Success: Database was successfully installed")

        # raising exceptions
        except Exception as e:
            LOGGER.exception("An exception occurred while creating the database: %s", e)
            LOGGER.error("Failed to create database due to the above exception")

    @staticmethod
    def add_ref_by_genebank_file(db_url, reference_gb, debug=False):
        """
        add reference
        """
        with sonarDBManager(db_url, readonly=False, debug=debug) as dbm:
            try:

                # adding reference
                if not reference_gb:
                    reference_gb = sonarUtils.get_default_reference_gb()
                records = [x for x in sonarUtils.iter_genbank(reference_gb)]
                sonarUtils._add_reference(dbm, records)
                return 0
            except Exception as e:
                LOGGER.exception(e)
                LOGGER.error("Fail to process GeneBank file")
                raise

    @staticmethod
    def connect_to_db(db: str, readonly: bool = True) -> sonarDBManager:
        """
        Connect to database.

        Args:
            db (str): The database to connect to.
            readonly (bool, optional): Open the database in readonly mode. Defaults to True.

        Returns:
            sonarDbManager: Database manager instance.
        """
        return sonarDBManager(db, readonly=readonly)

    @staticmethod
    def _create_reserved_properties(dbm: sonarDBManager) -> None:
        """Creates default properties in the database.

        Args:
            dbm (sonarDbManager): Database manager instance.
        """
        dbm.add_property(
            "IMPORTED",
            "date",
            "date",
            "date sample has been imported to the database",
            "sample",
            check_name=False,
        )
        dbm.add_property(
            "MODIFIED",
            "date",
            "date",
            "date when sample data has been modified lastly",
            "sample",
        )

    @staticmethod
    def _create_predefined_properties(dbm: sonarDBManager) -> None:
        """Creates predefined properties in the database.

        Args:
            dbm (sonarDbManager): Database manager instance.
        """
        properties = [
            ("SEQ_TECH", "text", "text", "Sequencing technologies"),
            ("PROCESSING_DATE", "date", "date", "Submission/Processing date"),
            ("COUNTRY", "text", "text", "Country where a sample belongs to"),
            ("HOST", "text", "text", "e.g., HUMAN"),
            ("ZIP", "text", "text", "zip code e.g., 33602"),
            ("LAB", "text", "text", "lab id e.g., 11069"),
            ("LINEAGE", "text", "text", "e.g., BA.2 or B.1.1.7"),
            ("TECHNOLOGY", "text", "text", "e.g., ILLUMINA"),
            (
                "GENOME_COMPLETENESS",
                "text",
                "text",
                "Genome completeness (e.g., partial or complete)",
            ),
            ("LENGTH", "integer", "numeric", "Genome lenght e.g., 197027"),
            ("COLLECTION_DATE", "date", "date", "Keep a sample collection date"),
        ]
        """
        dbm.add_property(
                    "GEO_LOCATION",
                    "text",
                    "text",
                    "Store the GEO location (if available e.g., USA: NY)",
        )

        """
        for prop in properties:
            dbm.add_property(*prop, "sample")

    # Reference handling
    @staticmethod
    def get_default_reference_gb() -> str:
        """Gets the default reference GenBank file.
        Returns:
            str: Absolute path to the reference GenBank file.
        """
        return os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "data", "ref.gb"
        )

    @staticmethod
    def _add_reference(dbm: sonarDBManager, records: List[Dict[str, Any]]) -> None:
        """Adds references to the database.

        Args:
            dbm (sonarDbManager): Database manager instance.
            records (List[Dict[str, Any]]): List of reference records.
        """
        ref_id = dbm.add_reference(
            records[0]["accession"],
            records[0]["description"],
            records[0]["organism"],
            1,
            1,
        )

        for i, record in enumerate(records):
            # add molecule
            mol_id = sonarUtils._add_molecule(dbm, ref_id, i, record)

            # add source
            source_id = sonarUtils._add_source(dbm, mol_id, record["source"])

            # add genes
            gene_ids = sonarUtils._add_genes(dbm, mol_id, record["gene"], source_id)
            # add cds
            sonarUtils._add_cds(dbm, mol_id, gene_ids, record["cds"])

    @staticmethod
    def _add_molecule(
        dbm: sonarDBManager, ref_id: int, i: int, record: Dict[str, Any]
    ) -> int:
        """Adds reference molecules and elements to the database.

        Args:
            dbm (sonarDbManager): Database manager instance.
            ref_id (int): Reference id.
            i (int): Index of the record.
            record (Dict[str, Any]): Reference record.
        Returns
            int: Molecule ID.
        """
        default = 1 if i == 0 else 0
        return dbm.insert_molecule(
            ref_id,
            record["moltype"],
            record["accession"],
            record["symbol"],
            record["description"],
            i,
            record["length"],
            default,
        )

    @staticmethod
    def _add_source(dbm: sonarDBManager, mol_id: int, source: Dict[str, Any]) -> int:
        """Handles source and inserts it into the database.

        Args:
            dbm (sonarDbManager): Database manager instance.
            mol_id (int): Molecule id.
            source (Dict[str, Any]): Source data.

        Returns:
            int: Source id.
        """
        source_id = dbm.insert_element(
            mol_id,
            "source",
            source["accession"],
            source["symbol"],
            source["description"],
            source["start"],
            source["end"],
            source["strand"],
            source["sequence"],
            standard=1,
            parts=source["parts"],
        )

        if source["sequence"] != dbm.get_sequence(source_id):
            LOGGER.error(
                f"Could not recover sequence of '{source['accession']}' (source) form Genbank file."
            )
            sys.exit(1)

        return source_id

    @staticmethod
    def _add_genes(
        dbm: sonarDBManager,
        mol_id: int,
        genes: List[Dict[str, Any]],
        source_id: int,
    ) -> Dict[str, int]:
        """Handles genes and inserts them into the database.

        Args:
            dbm (sonarDbManager): Database manager instance.
            mol_id (int): Molecule id.
            genes (List[Dict[str, Any]]): List of genes.
            source_id (int): Source id.

        Returns:
            Dict[str, int]: Dictionary of gene ids with gene accessions as keys.
        """
        gene_ids = {}
        for elem in genes:
            # QUESTION NOTE: some genomes have the repeated gene name
            # What should we do ???, if we skip these duplicated gene symbol
            # so in Elempart Table will not contain all region.
            if elem["accession"] in gene_ids:
                LOGGER.error(
                    f"Mutliple entries for '{elem['accession']}' (gene) in Genbank file."
                )
                # sys.exit(1)
                continue

            gene_ids[elem["accession"]] = dbm.insert_element(
                mol_id,
                "gene",
                elem["accession"],
                elem["symbol"],
                elem["description"],
                elem["start"],
                elem["end"],
                elem["strand"],
                elem["sequence"],
                standard=0,
                parent_id=source_id,
                parts=elem["parts"],
            )

            if elem["sequence"] != dbm.extract_sequence(
                gene_ids[elem["accession"]], molecule_id=mol_id
            ):

                # print(elem["sequence"])
                LOGGER.debug(f"Gene ID: {gene_ids}")
                LOGGER.error(
                    f"Could not recover sequence of '{elem['accession']}' (gene) from Genbank file"
                )
                sys.exit(1)

        return gene_ids

    @staticmethod
    def _add_cds(
        dbm: sonarDBManager,
        mol_id: int,
        gene_ids: Dict[str, int],
        cds: List[Dict[str, Any]],
        transl_table: Optional[int] = 1,
    ) -> None:
        """Handles coding sequences (CDS) and inserts them into the database.

        Args:
            dbm (sonarDbManager): Database manager instance.
            mol_id (int): Molecule id.
            gene_ids (Dict[str, int]): Dictionary of gene ids.
            cds (List[Dict[str, Any]]): List of coding sequences.
            transl_table (int, optional): Translation table to use.
        """
        for elem in cds:
            cds_id = dbm.insert_element(
                mol_id,
                "cds",
                elem["accession"],
                elem["symbol"],
                elem["description"],
                elem["start"],
                elem["end"],
                elem["strand"],
                elem["sequence"],
                0,
                gene_ids[elem["gene"]],
                elem["parts"],
            )

            if elem["sequence"] != dbm.extract_sequence(
                cds_id, translation_table=transl_table, molecule_id=mol_id
            ):
                LOGGER.error(
                    f"Could not recover sequence of '{elem['accession']}' (cds) from Genbank file"
                )
                sys.exit(1)

    # GENBANK PARSING
    @staticmethod
    def _process_segments(
        feat_location_parts: List[Union[FeatureLocation, CompoundLocation]],
        cds: bool = False,
    ) -> List[List[int]]:
        """
        Process the genomic regions (segments) of a feature.

        Args:
            feat_location_parts (List[Union[FeatureLocation, CompoundLocation]]): List of feature location parts.
            cds (bool): A flag indicating whether the segment corresponds to a coding sequence.
                        Default is False.

        Returns:
            segments (List[List[int]]): A list of processed segments. Each segment is represented
                                        as a list of integers [start, end, strand, base, index].
        """
        base = 0
        div = 1 if not cds else 3
        segments = []
        for i, segment in enumerate(feat_location_parts, 1):
            segments.append(
                [int(segment.start), int(segment.end), segment.strand, base, i]
            )
            base += round((segment.end - segment.start - 1) / div, 1)
        return segments

    @staticmethod
    def _extract_source_feature(gb_record: SeqRecord, gb_data: Dict) -> Dict:
        """
        Extract source feature from GenBank record.

        Args:
            gb_record: GenBank record.
            gb_data: Dictionary representing GenBank record.

        Returns:
            The updated GenBank data dictionary.

        Raises:
            ValueError: If SeqRecord does not contain exactly one 'source' feature.
        """
        source = [x for x in gb_record.features if x.type == "source"]
        if len(source) != 1:
            raise ValueError("Expecting exactly one source feature.")

        source = source[0]

        source_sequence = str(sonarBasics.harmonize_seq(source.extract(gb_record.seq)))
        source_parts = sonarUtils._process_segments(source.location.parts)
        gb_data.update(
            {
                "moltype": source.qualifiers.get("mol_type", [""])[0],
                "source": {
                    "accession": gb_data["accession"],
                    "symbol": gb_data["accession"],
                    "start": int(source.location.start),
                    "end": int(source.location.end),
                    "strand": "",
                    "sequence": source_sequence,
                    "description": "",
                    "parts": source_parts,
                },
                "length": len(source_sequence),
                "segment": source.qualifiers.get("segment", [""])[0],
            }
        )
        return gb_data

    @staticmethod
    def _extract_gene_feature(feature: SeqFeature, source_seq: str) -> dict:
        """
        Extracts the details from the gene feature of a genbank record.

        Args:
            feature (SeqFeature): A Biopython SeqFeature instance.
            source_seq (str): Source sequence.

        Returns:
            dict: A dictionary containing the extracted gene details.

        Raises:
            ValueError: If the feature type is not 'gene' or no qualifier for gene accession or symbol found.
        """
        if feature.type != "gene":
            raise ValueError("The provided feature is not a 'gene' feature.")

        if feature.id != "<unknown id>":
            accession = feature.id
        elif "gene" in feature.qualifiers:
            accession = feature.qualifiers["gene"][0]
        elif "locus_tag" in feature.qualifiers:
            accession = feature.qualifiers["locus_tag"][0]
        else:
            raise ValueError("No qualifier for gene accession found.")

        if "gene" in feature.qualifiers:
            symbol = feature.qualifiers["gene"][0]
        elif "locus_tag" in feature.qualifiers:
            symbol = feature.qualifiers["locus_tag"][0]
        else:
            raise ValueError("No qualifier for gene symbol found.")

        gene_details = {
            "accession": accession,
            "symbol": symbol,
            "start": int(feature.location.start),
            "end": int(feature.location.end),
            "strand": feature.strand,
            "sequence": sonarBasics.harmonize_seq(feature.extract(source_seq)),
            "description": "",
            "parts": sonarUtils._process_segments(feature.location.parts),
        }

        return gene_details

    @staticmethod
    def _extract_cds_feature(feature) -> dict:
        """
        Extracts the details from the CDS (Coding Sequence) feature of a genbank record.

        Args:
            feature (SeqFeature): A Biopython SeqFeature instance.

        Returns:
            dict: A dictionary containing the extracted CDS details.

        Raises:
            ValueError: If the feature type is not 'CDS'.
        """
        if feature.type != "CDS":
            raise ValueError("The provided feature is not a 'CDS' feature.")

        # for x in ["protein_id", "gene"]:
        #    if x not in feature.qualifiers:
        #         raise ValueError(f"Missing {x} qualifier for cds.")
        if feature.id != "<unknown id>":
            accession = feature.id
        elif "protein_id" in feature.qualifiers:
            accession = feature.qualifiers["protein_id"][0]
        elif "locus_tag" in feature.qualifiers:
            accession = feature.qualifiers["locus_tag"][0]
        else:
            raise ValueError("Missing protein_id/locus_tag qualifier for cds.")

        parts = sonarUtils._process_segments(feature.location.parts, True)
        accession = feature.qualifiers["protein_id"][0]
        symbol = (
            feature.qualifiers["gene"][0]
            if "gene" in feature.qualifiers
            else feature.qualifiers["locus_tag"][0]
        )
        sequence = feature.qualifiers.get("translation", [""])[0]
        description = feature.qualifiers.get("product", [""])[0]

        cds_details = {
            "accession": accession,
            "symbol": symbol,
            "start": int(feature.location.start),
            "end": int(feature.location.end),
            "strand": feature.strand,
            "gene": symbol,
            "sequence": sequence,
            "description": description,
            "parts": parts,
        }

        if sum([abs(x[1] - x[0]) for x in parts]) % 3 != 0:
            raise ValueError(f"The length of cds '{accession}' is not a multiple of 3.")

        return cds_details

    @staticmethod
    def iter_genbank(fname: str) -> Generator[Dict, None, None]:
        """
        Iterate over GenBank records in a file, yielding a dictionary representation of each record.

        small note on iter_genbank function
        1. At CDS and gene type, if "gene" key is not exist in dict, we use locus_tag instead
        (https://www.ncbi.nlm.nih.gov/genomes/locustag/Proposal.pdf). This also apply to accession
        in similar way.

        Args:
            fname: Name of the GenBank file.

        Yields:
            Dictionary representing a GenBank record.
        """

        for gb_record in SeqIO.parse(fname, "genbank"):
            gb_data = {}
            gb_data["accession"] = (
                gb_record.name + "." + str(gb_record.annotations["sequence_version"])
            )
            gb_data["symbol"] = gb_record.annotations.get("symbol", "")
            gb_data["organism"] = gb_record.annotations["organism"]
            gb_data["moltype"] = ""
            gb_data["description"] = gb_record.description
            gb_data["length"] = ""
            gb_data["segment"] = ""
            gb_data["gene"] = []
            gb_data["cds"] = []
            gb_data["source"] = ""

            gb_data = sonarUtils._extract_source_feature(
                gb_record, gb_data
            )  # assign data to source
            gb_data["gene"] = []
            gb_data["cds"] = []

            for feat in gb_record.features:
                if feat.type == "gene":
                    # pseudogene is unknown
                    if "pseudogene" in feat.qualifiers:
                        continue
                    gb_data["gene"].append(
                        sonarUtils._extract_gene_feature(
                            feat, gb_data["source"]["sequence"]
                        )
                    )
                elif feat.type == "CDS":
                    # when pseudogene is unknown

                    if "pseudogene" in feat.qualifiers:
                        continue
                    gb_data["cds"].append(sonarUtils._extract_cds_feature(feat))

            yield gb_data

    # DATA IMPORT
    @staticmethod
    def import_data(
        db: str,
        fasta: List[str] = [],
        csv_files: List[str] = [],
        tsv_files: List[str] = [],
        prop_links: List[str] = [],
        cachedir: str = None,
        autolink: bool = False,
        auto_anno: bool = False,
        progress: bool = False,
        update: bool = True,
        threads: int = 1,
        quiet: bool = False,
        reference: str = None,
        method: int = 1,
    ) -> None:
        """Import data from various sources into the database.

        Args:
            db: The database to import into.
            fasta: List of fasta files to import.
            csv_files: List of CSV files to import.
            tsv_files: List of TSV files to import.
            prop_links: List of column to property links (formatted as col=prop) to consider for import.
            cachedir: The directory to use for caching data during import.
            autolink: Whether to automatically link data.
            progress: Whether to show a progress bar during import.
            update: Whether to update existing records.
            threads: The number of threads to use for import.
            quiet: Whether to suppress logging.
        """
        sonarUtils._log_import_mode(update, quiet)

        # checks
        if not sonarBasics._files_exist(*fasta, *tsv_files, *csv_files):
            LOGGER.error("At least one provided file does not exist.")
            sys.exit(1)
        if not sonarUtils._is_import_required(fasta, tsv_files, csv_files, update):
            LOGGER.info("Nothing to import.")
            sys.exit(0)

        sonarUtils._check_reference(db, reference)

        # property handling
        prop_names = sonarUtils._get_prop_names(db, prop_links, autolink)

        # extract properties form csv/tsv files
        properties = sonarUtils._extract_props(csv_files, tsv_files, prop_names, quiet)

        # setup cache
        cache = sonarUtils._setup_cache(db, reference, cachedir, update, progress)

        # importing sequences
        if fasta:
            sonarUtils._import_fasta(
                fasta, properties, cache, threads, progress, method, auto_anno
            )

        # importing properties
        if csv_files or tsv_files:
            sonarUtils._import_properties(properties, db, progress)

    @staticmethod
    def _log_import_mode(update: bool, quiet: bool):
        """Log the current import mode."""
        if not quiet:
            LOGGER.info(
                "import mode: updating existing samples"
                if update
                else "import mode: skipping existing samples"
            )

    @staticmethod
    def _is_import_required(
        fasta: List[str], tsv_files: List[str], csv_files: List[str], update: bool
    ) -> bool:
        """Check if import is required."""
        if not fasta:
            if (not tsv_files and not csv_files) or not update:
                return False
        return True

    @staticmethod
    def _get_csv_colnames(fname: str, delim: str) -> List[str]:
        """
        Retrieve the column names of a CSV file.

        Args:
            fname: Filename of the CSV file.
            delim: Delimiter used in the CSV file.

        Returns:
            List of column names.
        """
        with sonarBasics.open_file_autodetect(fname) as file:
            return file.readline().strip().split(delim)

    @staticmethod
    def _get_properties_from_db(db: str) -> Set[str]:
        """Get the properties stored in the database."""
        with sonarUtils.connect_to_db(db) as dbm:
            db_properties = set(dbm.properties.keys())
        db_properties.add("sample")
        return db_properties

    @staticmethod
    def _extract_props(
        csv_files: List[str],
        tsv_files: List[str],
        prop_names: Dict[str, str],
        quiet: bool,
    ) -> Dict:
        """Process the CSV and TSV files."""
        properties = collections.defaultdict(dict)
        # check if necessary
        if not csv_files and not tsv_files:
            return properties

        # process files
        file_tuples = [(x, ",") for x in csv_files] + [(x, "\t") for x in tsv_files]
        for fname, delim in file_tuples:
            if not quiet:
                LOGGER.info("linking data from " + fname + "...")
            col_names = sonarUtils._get_csv_colnames(fname, delim)
            col_to_prop_links = sonarUtils._link_columns_to_props(
                col_names, prop_names, quiet
            )
            with sonarBasics.open_file_autodetect(fname) as handle:
                csvreader = csv.DictReader(handle, delimiter=delim)
                for row in csvreader:
                    sample = row[col_to_prop_links["sample"]]
                    for x, v in col_to_prop_links.items():
                        if x != "sample":
                            properties[sample][x] = row[v]

        return properties

    @staticmethod
    def _get_prop_names(
        db: str,
        prop_links: List[str],
        autolink: bool,
    ) -> Dict[str, str]:
        """get property names based on user input."""
        db_properties = sonarUtils._get_properties_from_db(db)
        propnames = {x: x for x in db_properties} if autolink else {}

        for link in prop_links:
            if link.count("=") != 1:
                LOGGER.error(
                    "'" + link + "' is not a valid column-to-property assignment."
                )
                sys.exit(1)
            prop, col = link.split("=")
            if prop == "SAMPLE":
                prop = "sample"
            if prop not in db_properties:
                LOGGER.error(
                    "Sample property '"
                    + prop
                    + "' is unknown to the selected database. Use list-props to see all valid properties."
                )
                sys.exit(1)
            propnames[prop] = col

        return propnames

    @staticmethod
    def _link_columns_to_props(
        col_names: List[str], prop_names: Dict[str, str], quiet: bool
    ) -> Dict[str, str]:
        """
        Link property columns to their corresponding database properties.

        Args:
            fields: List of column names in the metadata file.
            prop_names: Dictionary mapping database property names to column names in the metadata file.
            quiet: Boolean indicating whether to suppress print statements.

        Returns:
            Dictionary linking file columns (values) to database properties (keys).
        """
        links = {}
        props = sorted(prop_names.keys())
        for prop in props:
            prop_name = prop_names[prop]
            c = col_names.count(prop_name)
            if c == 1:
                links[prop] = prop_name
            elif c > 1:
                LOGGER.error(f"'{prop_name}' is not a unique column.")
                sys.exit(1)
        if "sample" not in links:
            LOGGER.error("Missing 'sample' column assignment.")
            sys.exit(1)
        elif len(links) == 1:
            LOGGER.error("The meta file does not provide any informative column.")
            sys.exit(1)
        if not quiet:
            for prop in props:
                if prop in links:
                    LOGGER.info("  " + prop + " <- " + links[prop])
                else:
                    LOGGER.info("  " + prop + " missing")
        return links

    @staticmethod
    def _import_fasta(
        fasta_files: List[str],
        properties: Dict,
        cache: sonarCache,
        threads: int = 1,
        progress: bool = False,
        method: int = 1,
        auto_anno: bool = False,
    ) -> None:
        """
        Process and import sequences from fasta files.

        Args:
            fasta_files: List of paths to fasta files.
            properties: Dictionary of properties linked to sample names.
            cache: Instance of sonarCache.
            threads: Number of threads to use for processing.
            progress: Whether to show progress bar.
            method: Alignment method 1 MAFFT , 2 Parasail
        """
        if not fasta_files:
            return

        cache.add_fasta(*fasta_files, properties=properties, method=method)

        # align sequences and process
        aligner = sonarAligner(cache_outdir=cache.basedir, method=method)
        l = len(cache._samplefiles_to_profile)
        with WorkerPool(n_jobs=threads, start_method="fork") as pool, tqdm(
            desc="profiling sequences...",
            total=l,
            unit="seqs",
            bar_format="{desc} {percentage:3.0f}% [{n_fmt}/{total_fmt}, {elapsed}<{remaining}, {rate_fmt}{postfix}]",
            disable=not progress,
        ) as pbar:
            for _ in pool.imap_unordered(
                aligner.process_cached_sample, cache._samplefiles_to_profile
            ):
                pbar.update(1)

        cache.import_cached_samples(threads, auto_anno=auto_anno)
        if method == 1:
            cache.clear_uncessary_cache(cache._samplefiles_to_profile)

    @staticmethod
    def _setup_cache(
        db: str,
        reference: str,
        cachedir: Optional[str] = None,
        update: bool = True,
        progress: bool = False,
        debug: bool = False,
    ) -> sonarCache:
        """Set up a cache for sequence data."""
        # Instantiate a sonarCache object.
        return sonarCache(
            db,
            outdir=cachedir,
            logfile="import.log",
            allow_updates=update,
            temp=not cachedir,
            debug=debug,
            disable_progress=not progress,
            refacc=reference,
        )

    @staticmethod
    def _import_properties(
        properties: Dict[str, Dict[str, str]], db: str, progress: bool
    ):
        """
        Imports properties to the database.

        Args:
            properties: A dictionary of properties, where the key is a sample name and
                        the value is another dictionary of properties for that sample.
            db: The database where the properties will be imported.
            progress: If True, displays a progress bar.
        """
        with sonarDBManager(db, readonly=False) as dbm:
            for sample_name in tqdm(
                properties,
                desc="Import data...",
                total=len(properties),
                unit="samples",
                bar_format="{desc} {percentage:3.0f}% [{n_fmt}/{total_fmt}, {elapsed}<{remaining}, {rate_fmt}{postfix}]",
                disable=not progress,
            ):
                sample_id = dbm.get_sample_id(sample_name)
                if not sample_id:
                    continue
                for property_name, value in properties[sample_name].items():
                    dbm.insert_property(sample_id, property_name, value)

    # MATCHING
    @staticmethod
    def match(
        db: str,
        profiles: List[str] = [],
        samples: List[str] = [],
        properties: Dict[str, str] = {},
        reference: Optional[str] = None,
        outfile: Optional[str] = None,
        output_column: Optional[List[str]] = [],
        format: str = "csv",
        showNX: bool = False,
        ignore_terminal_gaps: bool = True,
        frameshifts_only: bool = False,
    ):
        """
        Perform match operation and export the results.

        Args:
            db: Database name.
            profiles: List of profiles.
            samples: List of samples.
            properties: Dictionary of properties.
            reference: Reference accession.
            outfile: Output file path.
            output_column: List of output columns.
            format: Output format.
            showNX: Flag indicating whether to show NX.
            ignore_terminal_gaps: Flag indicating whether to terminal gaps.
            frameshifts_only: Flag indicating whether to only show frameshifts.

        Returns:
            None.
        """
        sonarUtils._check_reference(db, reference)
        with sonarDBManager(db) as dbm:
            if not reference:
                reference = dbm.get_default_reference_accession()
                LOGGER.info(f"Using Default Reference: {reference}")

            rows = dbm.match(
                profiles=profiles,
                samples=samples,
                reference_accession=reference,
                properties=properties,
                format=format,
                output_columns=output_column,
                filter_n=not showNX,
                filter_x=not showNX,
                frameshifts_only=frameshifts_only,
                ignore_terminal_gaps=ignore_terminal_gaps,
            )
            sonarUtils._export_query_results(
                rows, format, reference, outfile, output_column, db
            )

    @staticmethod
    def _export_query_results(
        cursor: object,
        format: str,
        reference: str,
        outfile: Optional[str],
        output_column: Optional[List[str]] = [],
        db: Optional[str] = None,
    ):
        """
        Export results depending on the specified format.

        Args:
            cursor: Cursor object.
            format: Output format.
            reference: Reference accession.
            outfile: Output file path.

        Returns:
            None.
        """
        if format in ["csv", "tsv"]:
            tsv = format == "tsv"
            sonarUtils.export_csv(
                cursor,
                output_column=output_column,
                outfile=outfile,
                na="*** no match ***",
                tsv=tsv,
            )
        elif format == "count":
            count = cursor
            if outfile:
                with open(outfile, "w") as handle:
                    handle.write(str(count))
            else:
                print(count)
        elif format == "vcf":
            sonarUtils.export_vcf(
                cursor,
                reference=reference,
                outfile=outfile,
                na="*** no match ***",
                db=db,
            )
        else:
            LOGGER.error(f"'{format}' is not a valid output format")
            sys.exit(1)

    # RESTORE SEQUENCES
    @staticmethod
    def restore_seq(  # noqa C901
        db: str,
        samples: Optional[List[str]],
        reference_accession: Optional[str] = None,
        aligned: bool = False,
        outfile: Optional[str] = None,
    ) -> None:
        """
        Restores the given samples from the database.

        Args:
            db: The database to restore samples from.
            samples: A list of samples to be restored.
            reference_accession: Reference accession if any.
            aligned: Whether the samples are aligned or not.
            outfile: If provided, the result will be written to this file.
        """
        reference_list = []
        with sonarDBManager(db, readonly=True) as dbm:

            # NOTE:Since we only want to restore fasta regardless of reference.
            # We select all references, and then we use only one of them
            # if the sample aligns with any.

            # get all references
            if reference_accession is None:
                reference_accession_dict = dbm.references
                for row in reference_accession_dict:
                    reference_list.append(row["accession"])
                LOGGER.debug(f"Query using reference: {reference_list}")

            gap = "-" if aligned else ""
            gap_alts = {" ", "."}

            with sonarBasics.out_autodetect(outfile) as handle:
                for sample in samples:
                    prefixes = collections.defaultdict(str)

                    # get reference-specific molecule sequences

                    if len(reference_list) > 0:  # find all possible alignments
                        for reference in reference_list:
                            alignment_data = dbm.get_alignment_data(
                                sample, reference_accession=reference
                            )
                            for x in alignment_data:
                                if x is not None:
                                    molecules = {
                                        x["element.id"]: {
                                            "seq": list(x["element.sequence"]),
                                            "mol": x["element.symbol"],
                                        }
                                    }
                                    # once we found it, no need to continually loop
                                    break
                    else:  # when the reference_accession is provided
                        molecules = {
                            x["element.id"]: {
                                "seq": list(x["element.sequence"]),
                                "mol": x["element.symbol"],
                            }
                            for x in dbm.get_alignment_data(
                                sample, reference_accession=reference_accession
                            )
                        }

                    if len(molecules) == 0:
                        LOGGER.info(
                            f"No {sample} with {reference_accession} is stored in the database"
                        )
                        continue

                    # restore stored mutations
                    for vardata in dbm.iter_dna_variants(sample, *molecules.keys()):
                        alt = vardata["variant.alt"]
                        start = vardata["variant.start"]
                        end = vardata["variant.end"]
                        elem_id = vardata["element.id"]
                        mol_symbol = molecules[elem_id]["mol"]

                        # inserting deletions
                        if alt in gap_alts:
                            for i in range(start, end):
                                molecules[elem_id]["seq"][i] = gap

                        # inserting snps and insertions
                        elif start >= 0:
                            if len(alt) > 1:
                                if aligned:
                                    alt = alt[1:].lower()
                                else:
                                    alt = alt[1:]
                                molecules[elem_id]["seq"][start] += alt
                            else:
                                molecules[elem_id]["seq"][start] = (
                                    alt + molecules[elem_id]["seq"][start][1:]
                                )
                        else:
                            prefixes[elem_id] = alt

                    # writing fasta output
                    molecules_len = len(molecules)
                    records = []
                    for elem_id in molecules:
                        if molecules_len == 1:
                            records.append(f">{sample}")
                        else:
                            records.append(f">{sample} [molecule={mol_symbol}]")
                        records.append(
                            prefixes[elem_id] + "".join(molecules[elem_id]["seq"])
                        )
                    if len(records) > 0:
                        handle.write("\n".join(records) + "\n")

    # DELETE OPERATION
    @staticmethod
    def del_ref(db, reference, debug):
        LOGGER.info("Start to delete....the process is not reversible.")
        with sonarDBManager(db, readonly=False, debug=debug) as dbm:

            # remove alignment
            samples_ids = dbm.get_samples_by_ref(reference)
            LOGGER.info(
                f"{len(samples_ids)} samples that linked to the reference will be also deleted"
            )
            # delete only reference will also delete the whole linked data.
            """
            if samples_ids:
                if debug:
                    logging.info(f"Delete: {samples_ids}")
                for sample in samples_ids:
                    # dbm.delete_seqhash(sample["seqhash"])
                    dbm.delete_alignment(
                        seqhash=sample["seqhash"], element_id=_ref_element_id
                    )
            """
            dbm.delete_reference(reference)

    @staticmethod
    def delete_sample(db: str, samples: List[str]) -> None:
        """
        Delete samples from the database.

        Args:
            db (str): The database to delete samples from.
            samples (list[str]): A list of samples to be deleted.
        """
        with sonarDBManager(db, readonly=False) as dbm:
            before = dbm.count_samples()
            dbm.delete_samples(*samples)
            after = dbm.count_samples()

            deleted = before - after
            LOGGER.info(f"{deleted} of {len(samples)} samples found and deleted.")
            LOGGER.info(f"{after} samples remain in the database.")

    # OTHER DB OPERATIONS
    @staticmethod
    def show_db_info(db: str, detailed: bool = False) -> None:
        """
        Show database information.

        Args:
            db (str): The database to show information for.
            detaield (bool): If True, print numbers of stored mutations.
        """
        with sonarDBManager(db, readonly=True) as dbm:
            print("Patho Version:                ", sonarBasics.get_version())
            print("database path:                   ", dbm.dbfile)
            print("database version:                ", dbm.get_db_version())
            print("database size:                   ", dbm.get_db_size())
            print("unique samples:                  ", dbm.count_samples())
            print("unique sequences:                ", dbm.count_sequences())
            if detailed:
                print("unique nucl-level mutations:      ", dbm.count_variants())
                print(
                    "unique prot-level mutations:      ",
                    dbm.count_variants(protein_level=True),
                )

    @staticmethod
    def direct_query(db: str, query: str, outfile: Optional[str] = None) -> None:
        """
        Directly query the database.

        Args:
            db: The database to query.
            query: The query to execute.
            outfile: If provided, the query result will be written to this file.
        """
        with sonarDBManager(db, readonly=True) as dbm:
            result = dbm.direct_query(query)
            sonarUtils.export_csv(result, outfile)

    # OUTPUT
    @staticmethod
    def export_csv(
        data: Union[List[Dict[str, Any]], Iterator[Dict[str, Any]]],
        output_column: Optional[List[str]] = [],
        outfile: Optional[str] = None,
        na: str = "*** no data ***",
        tsv: bool = False,
    ) -> None:
        """
        Export the results of a SQL query or a list of rows into a CSV file.

        Parameters:
        data: An iterator over the rows of the query result, or a list of rows.
        outfile: The path to the output file. If None, the output is printed to stdout.
        na: The string to print when no data is available.
        tsv: If True, the output is formatted as a TSV (Tab-Separated Values) file. Otherwise, it is formatted as a CSV (Comma-Separated Values) file.
        """
        # Convert list data to an iterator

        if isinstance(data, list):
            data_iter = iter(data)
        else:
            data_iter = data

        try:
            first_row = next(data_iter)
            # get only selected columns
            if output_column:
                first_row = {k: first_row[k] for k in output_column}
        except StopIteration:
            print(na)
            return

        with sonarBasics.out_autodetect(outfile) as handle:
            sep = "\t" if tsv else ","
            writer = csv.DictWriter(
                handle,
                fieldnames=first_row.keys(),
                delimiter=sep,
                lineterminator=os.linesep,
            )
            writer.writeheader()
            writer.writerow(first_row)

            for row in data_iter:
                if output_column:
                    row = {k: row[k] for k in output_column}
                writer.writerow(row)

    @staticmethod
    def _get_vcf_data(cursor) -> Dict:
        """
        Creates a data structure with records from a database cursor.

        Parameters:
        cursor: The cursor object from which to fetch data.

        Returns:
        records: A dictionary storing the genomic record data.
        all_samples: A sorted list of all unique samples in the records.
        """
        # Initialize the nested dictionary for storing records
        records = collections.defaultdict(
            lambda: collections.defaultdict(lambda: collections.defaultdict(dict))
        )
        all_samples = set()

        for row in cursor:
            # Split out the data from each row
            chrom, pos, pre_ref, ref, alt, samples = (
                row["molecule.accession"],
                row["variant.start"],
                row["variant.pre_ref"],
                row["variant.ref"],
                row["variant.alt"],
                row["samples"],
            )

            # Convert the samples string into a set
            sample_set = set(samples.split("\t"))
            # POS position in VCF format: 1-based position
            pos = pos + 1
            # Skip the empty alternate values

            records[chrom][pos][ref][alt] = sample_set

            if pre_ref not in records[chrom][pos]:
                records[chrom][pos]["pre_ref"] = pre_ref
            # Update the list of all unique samples
            all_samples.update(sample_set)

        return records, sorted(all_samples)

    def _write_vcf_header(handle, reference: str, all_samples: List[str]):
        """
        Writes the VCF file header to the given file handle.

        Parameters:
        handle: The file handle to which to write the header.
        reference: The reference genome name.
        all_samples: A list of all unique sample names.
        """
        handle.write("##fileformat=VCFv4.2\n")
        handle.write("##poweredby=PathSonar\n")
        handle.write(f"##reference={reference}\n")
        handle.write('##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype"\n')
        handle.write(
            "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t"
            + "\t".join(all_samples)
            + "\n"
        )

    def _write_vcf_records(handle, records: Dict, all_samples: List[str]):
        """
        Writes the VCF file records to the given file handle.

        Parameters:
        handle: The file handle to which to write the records.
        vcf_data: The dictionary storing the genomic record data.
        all_samples: A list of all unique sample names.
        """
        # Loop through each level of the dictionary to construct and write the VCF records
        for chrom in records:
            for pos in records[chrom]:
                for ref in records[chrom][pos]:

                    if ref == "pre_ref":  # skip pre_ref key
                        continue
                    # snps and inserts (combined output)
                    alts = [x for x in records[chrom][pos][ref].keys() if x.strip()]
                    if alts:
                        alt_samples = set()
                        gts = []
                        for alt in alts:
                            samples = records[chrom][pos][ref][alt]
                            alt_samples.update(samples)
                            gts.append(
                                ["1" if x in samples else "0" for x in all_samples]
                            )
                        gts = [
                            ["0" if x in alt_samples else "1" for x in all_samples]
                        ] + gts
                        record = [
                            chrom,
                            str(pos),
                            ".",
                            ref,
                            ",".join(alts),
                            ".",
                            ".",
                            ".",
                            "GT",
                        ] + ["/".join(x) for x in zip(*gts)]

                    # dels (individual output)

                    for alt in [
                        x for x in records[chrom][pos][ref].keys() if not x.strip()
                    ]:
                        pre_ref = records[chrom][pos]["pre_ref"]
                        samples = records[chrom][pos][ref][alt]
                        record = [
                            chrom,
                            str(
                                1 if pos - 1 <= 0 else pos - 1
                            ),  # -1 to the position for DEL, NOTE: be careful for 0-1=-1
                            ".",
                            (pre_ref + ref),
                            (pre_ref) if alt == " " else alt,  # changed form '.'
                            ".",
                            ".",
                            ".",
                            "GT",
                        ] + ["0/1" if x in samples else "./." for x in all_samples]
                    handle.write("\t".join(record) + "\n")

    def export_vcf(
        cursor,
        reference: str,
        outfile: Optional[str] = None,
        na: str = "*** no match ***",
        generate_hash_file_flag: bool = True,
        db: Optional[str] = None,
    ):  # noqa: C901
        """
        Exports data from a database result to a VCF file.

        Parameters:
        cursor: The rows object which already has been fetched data.
        reference: The reference genome name.
        outfile: The output file name. If None, output is printed to stdout.
        na: The string to print if there are no records.
        """

        if not cursor:
            print(na)
        else:
            records, all_samples = sonarUtils._get_vcf_data(cursor)
            if outfile is not None:
                # The below code is used in import process.
                # Extract the directory path from the outfile
                directory_path = os.path.dirname(outfile)
                if directory_path and not os.path.exists(directory_path):
                    os.makedirs(directory_path, exist_ok=True)

                sample_hash_list = {}
                IDs_list = {}
                # Create Sample seqhash and variant
                for row in cursor:  # sonarBasics.iter_formatted_match(cursor):
                    # print(row)
                    element_id, variant_id, samples = (
                        row["element.id"],
                        row["variant.id"],
                        row["samples"],
                    )
                    samples = samples.split(",")
                    # find samples and seqhash
                    with sonarDBManager(db, readonly=True) as dbm:

                        for sample in samples:
                            seqhash = dbm.get_seq_hash(sample)
                            # handle the hash and sample.
                            sample_hash_list[sample] = seqhash["seqhash"]
                            # handle the variant and sample.
                            if sample not in IDs_list:
                                IDs_list[sample] = []
                            IDs_list[sample].append(
                                {"element_id": element_id, "variant_id": variant_id}
                            )
                # Combine sonar_hash and reference into a single dictionary
                data = {
                    "sample_variantTable": IDs_list,
                    "sample_hashes": sample_hash_list,
                    "reference": reference,
                }

                # Remove the existing extension from outfile and then append a new extension.
                filename_sonarhash = get_filename_sonarhash(outfile)
                with open(filename_sonarhash, "w") as file:
                    json.dump(data, file)

            with sonarBasics.out_autodetect(outfile) as handle:
                sonarUtils._write_vcf_header(handle, reference, all_samples)
                sonarUtils._write_vcf_records(handle, records, all_samples)

    @staticmethod
    def process_annotation(db, paired_list, progress=False):  # noqa: C901
        """
        Steps:
            1. Read annotated txt file and .sonar_hash
            2. Get alignment ID and source element ID
            3. Get variant ID
            4. Insert the 3 IDs into the database.

        Input:
            paired_list = (annotated_file, sonar_hash_file)

        """
        with sonarDBManager(db, readonly=False) as dbm:
            for _tuple in paired_list:
                annotated_file, sonar_hash_file = _tuple
                annotated_df = read_tsv_snpSift(annotated_file)
                sonar_hash = read_sonar_hash(sonar_hash_file)
                reference_accession = sonar_hash["reference"]
                sample_dict = sonar_hash["sample_hashes"]
                sample_variant_dict = sonar_hash["sample_variantTable"]

                # Step 2
                for sample_key in sample_dict:
                    hash_value = sample_dict[sample_key]
                    source_ids_list = dbm.get_element_ids(reference_accession, "source")

                    if len(source_ids_list) > 1:
                        LOGGER.error("There is a duplicated element ID!!")
                        sys.exit(1)
                    else:
                        source_element_id = source_ids_list[0]

                    alnids = dbm.get_alignment_id(hash_value, source_element_id)

                    if type(alnids) is list:
                        LOGGER.error(
                            f"Hash value: {hash_value} is not found in the database!!"
                        )
                        sys.exit(1)
                    else:
                        alignment_id = alnids

                    # Step 3
                    sample_variant_list = sample_variant_dict[sample_key]

                    # NOTE: MemoryError can be raised if a huge list is converted to a DataFrame
                    _df = pd.DataFrame.from_dict(sample_variant_list)

                    for row in _df.itertuples():
                        variant_id = getattr(row, "variant_id")

                        selected_var = dbm.get_variant_by_id(variant_id)
                        if selected_var is None:
                            LOGGER.error("No variant was found")
                            LOGGER.warning(
                                "This can happen when using a differnet version of database or database instance."
                            )
                            LOGGER.info(
                                "Please ensure data import from the corresponding database version."
                            )
                            sys.exit(1)
                        # ref = selected_var["ref"]

                        # VCF: 1-based position
                        # For DEL, we dont do +1
                        ref = (
                            (selected_var["pre_ref"] + selected_var["ref"])
                            if selected_var["alt"] == " "
                            else selected_var["ref"]
                        )

                        if selected_var["alt"] == " ":
                            if selected_var["start"] == 0:
                                start = 1
                            else:
                                start = selected_var["start"]
                        else:
                            start = selected_var["start"] + 1

                        if selected_var["alt"] == " ":
                            if selected_var["start"] == 0:
                                alt = "."
                            else:
                                alt = selected_var["pre_ref"]
                        else:
                            alt = selected_var["alt"]

                        # Handle different kind of SNV (Nucleotide symbol).
                        if alt != "." and len(alt) == 1:
                            alt = sonarDBManager.IUPAC_CODES["nt"][alt.upper()]

                        else:
                            alt = [alt]
                        # Check if it exists in the annotated txt file.
                        selected_rows = annotated_df.loc[
                            (annotated_df["POS"] == start)
                            & (annotated_df["REF"] == ref)
                            & (annotated_df["ALT"].isin(alt))
                        ]
                        # If it does not return any result or more than 1, we should raise an error because
                        # the wrong annotated text file is being used or the database has already been modified.

                        if len(selected_rows) == 0:
                            LOGGER.error(
                                "It appears that the wrong annotated text file is being used "
                                "or the .sonar_hash file is not match to the input "
                                "or the database has already been modified. Please double-check the file "
                                "or database!"
                            )
                            LOGGER.info("Get VAR:")
                            LOGGER.info(selected_var)
                            LOGGER.info("Use for searching a ROW:")
                            LOGGER.info(f"start:{start} , ref:{ref} , alt:{alt}")
                            LOGGER.info("Get DF:")
                            LOGGER.info(f"{annotated_df[annotated_df['POS'] == start]}")
                            sys.exit(1)

                        # Find associated ID from annotationTable.
                        for index, row in selected_rows.iterrows():

                            effect = row["EFFECT"]

                            if effect is None or effect == ".":
                                effect = ""  # Default
                            effect_id = dbm.get_annotation_ID_by_type(effect)

                            # Step 4
                            # Insert into the database
                            dbm.insert_alignment2annotation(
                                variant_id, alignment_id, effect_id
                            )

    @staticmethod
    def _check_reference(db, reference):

        with sonarDBManager(db, readonly=True) as dbm:
            reference_accession_dict = dbm.references
            accession_list = [entry["accession"] for entry in reference_accession_dict]

        if reference is not None and reference not in accession_list:
            LOGGER.error(f"The reference {reference} does not exist.")
            sys.exit(1)
