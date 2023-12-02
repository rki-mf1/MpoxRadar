#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# author: Stephan Fuchs (Robert Koch Institute, MF1, fuchss@rki.de)
# , Kunaphas (RKI-MF1, HPI, kunaphas.kon@gmail.com)

import argparse
import os
import sys
from textwrap import fill
from typing import Optional

from tabulate import tabulate

from .basics import sonarBasics
from .config import DB_URL
from .dbm import sonarDBManager
from .dev import fix_annotation
from .dev import fix_element_id_NT
from .dev import fix_pre_ref
from .dev import test_align_mafft
from .logging import LoggingConfigurator
from .utils import sonarUtils

# from pathosonar.linmgr import sonarLinmgr

# from .cache import sonarCache  # noqa: F401

VERSION = sonarBasics.get_version()

# Initialize logger
LOGGER = LoggingConfigurator.get_logger()


class args_namespace(object):
    """An empty class for storing command-line arguments as object attributes."""

    pass


def parse_args(args=None):
    """
    Parse command-line arguments using argparse.ArgumentParser.

    Args:
        args (list): List of command-line arguments. Default is None.
        namespace (argparse.Namespace): An existing namespace to populate with parsed arguments. Default is None.

    Returns:
        argparse.Namespace: Namespace containing parsed command-line arguments.
    """

    # preparations
    user_namespace = args_namespace()
    parser = argparse.ArgumentParser(
        prog="sonar",
        description=f"pathSonar {VERSION}: Integrated Genome Information System for Pathogen Surveillance ",
    )

    # parser components
    # Create parent parsers for common arguments and options for the command-line interface
    general_parser = create_parser_general()
    database_parser = create_parser_database()
    output_parser = create_parser_output()
    sample_parser = create_parser_sample()
    property_parser = create_parser_property()
    reference_parser = create_parser_reference()
    thread_parser = create_parser_thread()

    # Create all subparsers for the command-line interface
    subparsers = parser.add_subparsers(dest="command", required=True)

    # setup parser
    subparsers, _ = create_subparser_setup(subparsers, reference_parser)
    # import parser
    subparsers, _ = create_subparser_import(
        subparsers, database_parser, thread_parser, reference_parser
    )

    # Reference parser
    subparsers, _ = create_subparser_list_reference(subparsers, database_parser)
    subparsers, _ = create_subparser_add_reference(subparsers, database_parser)
    subparsers, _ = create_subparser_delete_reference(
        subparsers, database_parser, reference_parser
    )

    subparsers, _ = create_subparser_list_prop(subparsers, database_parser)
    subparsers, _ = create_subparser_add_prop(
        subparsers, database_parser, property_parser
    )
    subparsers, _ = create_subparser_delete_prop(
        subparsers, database_parser, property_parser
    )

    subparsers, _ = create_subparser_delete(subparsers, database_parser, sample_parser)

    subparsers, subparser_match = create_subparser_match(
        subparsers,
        database_parser,
        reference_parser,
        sample_parser,
        output_parser,
        general_parser,
    )

    subparsers, _ = create_subparser_restore(
        subparsers,
        database_parser,
        sample_parser,
        output_parser,
        reference_parser,
        general_parser,
    )
    subparsers, _ = create_subparser_info(subparsers, database_parser)
    subparsers, _ = create_subparser_optimize(subparsers, database_parser)
    subparsers, _ = create_import_anno(subparsers, database_parser)
    subparsers, _ = create_subparser_direct_query(
        subparsers, database_parser, output_parser
    )
    # subparsers, _ = create_subparser_db_upgrade(subparsers, database_parser)
    # dev parser
    parser_dev = subparsers.add_parser("dev", help="To perform admin tasks.")

    parser_dev.add_argument(
        "--up_vartype",
        help="update variant type, this will annotate NT variant (SNV,INDEL,Frameshift)",
        action="store_true",
    )
    parser_dev.add_argument(
        "--up_ele_nt",
        help="update element_id at VariantTable, this will fix element symbol of NT.",
        action="store_true",
    )
    parser_dev.add_argument(
        "--up_pre_ref",
        help="update pre-char of ref. column, this will add the character position before ref. column.",
        action="store_true",
    )
    # db-upgrade parser
    # subparsers.add_parser(
    #    "db-upgrade",
    #    parents=[general_parser],
    #    help="upgrade a database to the latest version",
    # )

    # version parser
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="[Multi aligners] pathoSonar " + VERSION,
        help="Show program's version number and exit.",
    )

    # register known arguments
    # add database-specific properties to match subparser
    user_namespace = args_namespace()
    known_args, _ = parser.parse_known_args(args=args, namespace=user_namespace)
    if is_match_selected(known_args):
        LoggingConfigurator(debug=known_args.debug)
        with sonarDBManager(known_args.db, readonly=True) as db_manager:
            for property in db_manager.properties.values():
                subparser_match.add_argument(
                    "--" + property["name"], type=str, nargs="+"
                )

    return parser.parse_args(args=args, namespace=user_namespace)


def is_match_selected(namespace: Optional[argparse.Namespace] = None) -> bool:
    """
    Checks if the 'match' command is selected and the 'db' attribute is present in the arguments.

    Args:
        namespace: Namespace object for storing argument values (default: None)

    Returns:
        True if 'match' command is selected and 'db' attribute is present, False otherwise
    """
    # Check if the 'match' command is selected and the 'db' attribute is present
    match_selected = namespace.command == "match" and hasattr(namespace, "db")

    return match_selected


def check_file(fname, exit_on_fail=True):
    """
    Check if a given file path exists.

    Args:
        fname (string): The name and path to an existing file.
        exit_on_fail (boolean): Whether to exit the script if the file doesn't exist. Default is True.

    Returns:
        True if the file exists, False otherwise.
    """
    if not os.path.isfile(fname):
        if exit_on_fail:
            sys.exit("Error: The file '" + fname + "' does not exist.")
        return False
    return True


def create_subparser_direct_query(
    subparsers: argparse._SubParsersAction, *parent_parsers: argparse.ArgumentParser
) -> argparse.ArgumentParser:
    """
    Creates an 'direct-query' subparser with command-specific arguments and options for the command-line interface.

    Args:
        subparsers (argparse._SubParsersAction): ArgumentParser object to attach the 'direct-query' subparser to.
        parent_parsers (argparse.ArgumentParser): ArgumentParser objects providing common arguments and options.

    Returns:
        argparse.ArgumentParser: The created 'direct-query' subparser.
    """
    parser = subparsers.add_parser(
        "direct-query",
        help="connect read-only to the database for direct queries",
        parents=parent_parsers,
    )
    parser.add_argument(
        "--sql",
        help="SQL query/command/statement  (e.g., --sql 'SELECT * FROM SAMPLE')",
        type=str,
        required=True,
    )
    return subparsers, parser


def create_parser_general() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--debug",
        help="activate debugging mode showing all queries and debug info on screen",
        action="store_true",
    )
    return parser


def create_parser_database() -> argparse.ArgumentParser:
    """Creates a 'database' parent parser with common arguments and options for the command-line interface.

    Returns:
        argparse.ArgumentParser: The created 'database' parent parser.
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--db", metavar="FILE/URL", help="path/url to Sonar database", type=str
    )
    return parser


def create_parser_output() -> argparse.ArgumentParser:
    """Creates an 'output' parent parser with common arguments and options for the command-line interface.

    Returns:
        argparse.ArgumentParser: The created 'output' parent parser.
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "-o",
        "--out",
        metavar="FILE",
        help="write output file (existing files will be overwritten!)",
        type=str,
        default=None,
    )

    parser.add_argument(
        "--out-column",
        help="select output columns to the output file (support csv and tsv)",
        type=str,
        default="all",
    )
    return parser


def create_parser_sample() -> argparse.ArgumentParser:
    """Creates a 'sample' parent parser with common arguments and options for the command-line interface.

    Returns:
        argparse.ArgumentParser: The created 'sample' parent parser.
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--sample",
        metavar="STR",
        help="sample accession(s) to consider",
        type=str,
        nargs="+",
        default=[],
    )
    parser.add_argument(
        "--sample-file",
        metavar="FILE",
        help="file containing sample accession(s) to consider (one per line)",
        type=str,
        nargs="+",
        default=[],
    )
    return parser


def create_parser_property() -> argparse.ArgumentParser:
    """Creates a 'property' parent parser with common arguments and options for the command-line interface.

    Returns:
        argparse.ArgumentParser: The created 'property' parent parser.
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--name", metavar="STR", help="property name", type=str, required=True
    )
    return parser


def create_parser_reference() -> argparse.ArgumentParser:
    """Creates a 'reference' parent parser with common arguments and options for the command-line interface.

    Returns:
        argparse.ArgumentParser: The created 'reference' parent parser.
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "-r",
        "--reference",
        metavar="STR",
        help="reference accession",
        type=str,
        default=None,
    )
    return parser


def create_parser_thread() -> argparse.ArgumentParser:
    """Creates a 'thread' parent parser with common arguments and options for the command-line interface.

    Returns:
        argparse.ArgumentParser: The created 'thread' parent parser.
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "-t",
        "--threads",
        metavar="INT",
        help="number of threads to use (default: 1)",
        type=int,
        default=1,
    )
    return parser


def create_subparser_setup(
    subparsers: argparse._SubParsersAction, *parent_parsers: argparse.ArgumentParser
) -> argparse.ArgumentParser:
    """
    Creates a 'setup' subparser with command-specific arguments and options for the command-line interface.

    Args:
        subparsers (argparse._SubParsersAction): ArgumentParser object to attach the 'setup' subparser to.
        parent_parsers (argparse.ArgumentParser): ArgumentParser objects providing common arguments and options.

    Returns:
        argparse.ArgumentParser: The created 'setup' subparser.
    """
    parser = subparsers.add_parser(
        "setup", help="set up a new database", parents=parent_parsers
    )
    parser.add_argument(
        "--default-props",
        help="add commonly used properties to the new database",
        action="store_true",
    )
    parser.add_argument(
        "--gbk",
        metavar="GBK_FILE",
        help="path to GenBank reference file (NC_063383.1. is used as default reference)",
        type=str,
        default=None,
    )
    return subparsers, parser


def create_subparser_import(
    subparsers: argparse._SubParsersAction, *parent_parsers: argparse.ArgumentParser
) -> argparse.ArgumentParser:
    """
    Creates an 'import' subparser with command-specific arguments and options for the command-line interface.

    Args:
        subparsers (argparse._SubParsersAction): ArgumentParser object to attach the 'import' subparser to.
        parent_parsers (argparse.ArgumentParser): ArgumentParser objects providing common arguments and options.

    Returns:
        argparse.ArgumentParser: The created 'import' subparser.
    """
    parser = subparsers.add_parser(
        "import",
        help="import genome sequences and sample properties into the database",
        parents=parent_parsers,
    )

    parser.add_argument(
        "--method",
        help="Select alignment tools: 1. MAFFT 2. Parasail (default 1)",
        type=int,
        default=1,
    )

    parser.add_argument(
        "--fasta",
        help="fasta file containing genome sequences to import",
        type=str,
        nargs="+",
        default=None,
    )
    parser.add_argument(
        "--tsv",
        metavar="TSV_FILE",
        help="tab-delimited file containing sample properties to import",
        type=str,
        nargs="+",
        default=[],
    )
    parser.add_argument(
        "--csv",
        metavar="CSV_FILE",
        help="comma-delimited file containing sample properties to import",
        type=str,
        nargs="+",
        default=[],
    )
    parser.add_argument(
        "--cols",
        help="assign column names used in the provided TSV/CSV file to the matching property names provided by the database in the form PROP=COL (e.g. SAMPLE=GenomeID)",
        type=str,
        nargs="+",
        default=[],
    )
    parser.add_argument(
        "--auto-link",
        help="automatically link TSV/CSV columns with database fields based on identical names",
        action="store_true",
    )
    parser.add_argument(
        "--auto-anno",
        help="automatically annotate sample with SnpEff tool.",
        action="store_true",
    )
    parser.add_argument(
        "--no-update",
        help="skip samples already existing in the database",
        action="store_true",
    )
    parser.add_argument(
        "--cache",
        metavar="DIR",
        help="directory for chaching data (default: a temporary directory is created)",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--no-progress",
        "-p",
        help="don't show progress bars while importing",
        action="store_true",
    )
    return subparsers, parser


def create_subparser_list_prop(
    subparsers: argparse._SubParsersAction, *parent_parsers: argparse.ArgumentParser
) -> argparse.ArgumentParser:
    """
    Creates a 'list-prop' subparser with command-specific arguments and options for the command-line interface.

    Args:
        subparsers (argparse._SubParsersAction): ArgumentParser object to attach the 'list-prop' subparser to.
        parent_parsers (argparse.ArgumentParser): ArgumentParser objects providing common arguments and options.

    Returns:
        argparse.ArgumentParser: The created 'list-prop' subparser.
    """
    parser = subparsers.add_parser(
        "list-prop",
        help="view sample properties added to the database",
        parents=parent_parsers,
    )
    return subparsers, parser


def create_subparser_add_prop(
    subparsers: argparse._SubParsersAction, *parent_parsers: argparse.ArgumentParser
) -> argparse.ArgumentParser:
    """
    Creates an 'add-prop' subparser with command-specific arguments and options for the command-line interface.

    Args:
        subparsers (argparse._SubParsersAction): ArgumentParser object to attach the 'add-prop' subparser to.
        parent_parsers (argparse.ArgumentParser): ArgumentParser objects providing common arguments and options.

    Returns:
        argparse.ArgumentParser: The created 'add-prop' subparser.
    """
    parser = subparsers.add_parser(
        "add-prop", help="add a property to the database", parents=parent_parsers
    )
    parser.add_argument(
        "--descr",
        metavar="STR",
        help="a short description of the property",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--dtype",
        metavar="STR",
        help="the data type of the property",
        type=str,
        choices=["integer", "float", "text", "date", "zip", "pango"],
        required=True,
    )
    parser.add_argument(
        "--qtype",
        metavar="STR",
        help="the query type of the property",
        type=str,
        choices=["numeric", "float", "text", "date", "zip", "pango"],
        default=None,
    )
    parser.add_argument(
        "--default",
        metavar="VAR",
        help="the default value of the property (none by default)",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--subject",
        metavar="VAR",
        help="choose between sample or variant property (by default: sample)",
        choices=["sample", "variant"],
        default="sample",
    )

    return subparsers, parser


def create_subparser_delete_prop(
    subparsers: argparse._SubParsersAction, *parent_parsers: argparse.ArgumentParser
) -> argparse.ArgumentParser:
    """
    Creates an 'delete-prop' subparser with command-specific arguments and options for the command-line interface.

    Args:
        subparsers (argparse._SubParsersAction): ArgumentParser object to attach the 'delete-prop' subparser to.
        parent_parsers (argparse.ArgumentParser): ArgumentParser objects providing common arguments and options.

    Returns:
        argparse.ArgumentParser: The created 'delete-prop' subparser.
    """
    parser = subparsers.add_parser(
        "delete-prop", help="delete a property to the database", parents=parent_parsers
    )
    parser.add_argument(
        "--force",
        help="skip user confirmation and force property to be deleted",
        action="store_true",
    )
    return subparsers, parser


def create_subparser_delete(
    subparsers: argparse._SubParsersAction, *parent_parsers: argparse.ArgumentParser
) -> argparse.ArgumentParser:
    """
    Creates an 'delete' subparser with command-specific arguments and options for the command-line interface.

    Args:
        subparsers (argparse._SubParsersAction): ArgumentParser object to attach the 'delete' subparser to.
        parent_parsers (argparse.ArgumentParser): ArgumentParser objects providing common arguments and options.

    Returns:
        argparse.ArgumentParser: The created 'delete' subparser.
    """
    parser = subparsers.add_parser(
        "delete", help="delete samples from the database", parents=parent_parsers
    )
    return subparsers, parser


def create_subparser_match(
    subparsers: argparse._SubParsersAction, *parent_parsers: argparse.ArgumentParser
) -> argparse.ArgumentParser:
    """
    Creates a 'match' subparser with command-specific arguments and options for the command-line interface.

    Args:
        subparsers (argparse._SubParsersAction): An ArgumentParser object to attach the 'match' subparser to.
        parent_parsers (argparse.ArgumentParser): A list of ArgumentParser objects providing common arguments and options.

    Returns:
        argparse.ArgumentParser: The created 'match' subparser.
    """
    parser = subparsers.add_parser(
        "match",
        help="match samples based on mutation profiles and/or properties",
        parents=parent_parsers,
    )

    parser.add_argument(
        "--profile",
        "-p",
        metavar="STR",
        help="match genomes sharing the given mutation profile",
        type=str,
        action="append",
        nargs="+",
        default=[],
    )
    parser.add_argument(
        "--showNX",
        help="include non-informative polymorphisms in resulting mutation profiles (X for AA and N for NT)",
        action="store_true",
    )
    parser.add_argument(
        "--frameshifts-only",
        help="match only mutation profiles with frameshift mutations",
        action="store_true",
    )
    parser.add_argument(
        "--out-cols",
        metavar="STR",
        help="define output columns for CSV and TSV files (by default all available columns are shown)",
        type=str,
        nargs="+",
        default=[],
    )
    mutually_exclusive_group = parser.add_mutually_exclusive_group()
    mutually_exclusive_group.add_argument(
        "--count", help="count matching genomes only", action="store_true"
    )
    mutually_exclusive_group.add_argument(
        "--format",
        help="output format (default: tsv)",
        choices=["csv", "tsv", "vcf"],
        default="tsv",
    )
    return subparsers, parser


def create_subparser_restore(
    subparsers: argparse._SubParsersAction, *parent_parsers: argparse.ArgumentParser
) -> argparse.ArgumentParser:
    """
    Creates a 'restore' subparser with command-specific arguments and options for the command-line interface.

    Args:
        subparsers (argparse._SubParsersAction): An ArgumentParser object to attach the 'restore' subparser to.
        parent_parsers (argparse.ArgumentParser): A list of ArgumentParser objects providing common arguments and options.

    Returns:
        argparse.ArgumentParser: The created 'restore' subparser.
    """
    parser = subparsers.add_parser(
        "restore",
        help="restore genome sequences from the database",
        parents=parent_parsers,
    )
    parser.add_argument(
        "--aligned",
        help='use pairwise aligned form (deletions indicated by "-" and insertions by lowercase letters)',
        action="store_true",
    )
    return subparsers, parser


def create_subparser_info(
    subparsers: argparse._SubParsersAction, *parent_parsers: argparse.ArgumentParser
) -> argparse.ArgumentParser:
    """
    Creates a 'info' subparser with command-specific arguments and options for the command-line interface.

    Args:
        subparsers (argparse._SubParsersAction): An ArgumentParser object to attach the 'info' subparser to.
        parent_parsers (argparse.ArgumentParser): A list of ArgumentParser objects providing common arguments and options.

    Returns:
        argparse.ArgumentParser: The created 'info' subparser.
    """
    parser = subparsers.add_parser(
        "info",
        help="show detailed information on a given database",
        parents=parent_parsers,
    )
    parser.add_argument(
        "--detailed",
        help="show numbers of stored mutations (dependent on database size this might take a while to process)",
        action="store_true",
    )
    return subparsers, parser


def create_subparser_optimize(
    subparsers: argparse._SubParsersAction, *parent_parsers: argparse.ArgumentParser
) -> argparse.ArgumentParser:
    """
    Creates an 'optimize' subparser with command-specific arguments and options for the command-line interface.

    Args:
        subparsers (argparse._SubParsersAction): ArgumentParser object to attach the 'optimize' subparser to.
        parent_parsers (argparse.ArgumentParser): ArgumentParser objects providing common arguments and options.

    Returns:
        argparse.ArgumentParser: The created 'optimize' subparser.
    """
    parser = subparsers.add_parser(
        "optimize",
        help="optimize database (e.g., rearranges data for efficient storage and faster queries, eliminating unnecessary space.)",
        parents=parent_parsers,
    )
    parser.add_argument(
        "--tempdir",
        help="custom temporrary directory (default: None)",
        type=str,
        default=None,
    )
    return subparsers, parser


def create_subparser_list_reference(
    subparsers: argparse._SubParsersAction, *parent_parsers: argparse.ArgumentParser
) -> argparse.ArgumentParser:

    # View Reference.
    parser = subparsers.add_parser(
        "list-ref",
        parents=parent_parsers,
        help="List all references in database.",
    )
    return subparsers, parser


def create_subparser_add_reference(
    subparsers: argparse._SubParsersAction, *parent_parsers: argparse.ArgumentParser
) -> argparse.ArgumentParser:

    parser = subparsers.add_parser(
        "add-ref",
        parents=parent_parsers,
        help="Add reference sequence to the database.",
    )
    parser.add_argument(
        "--gbk",
        metavar="FILE",
        help="genbank file of a reference genome",
        type=str,
        required=True,
    )

    return subparsers, parser


def create_subparser_delete_reference(
    subparsers: argparse._SubParsersAction, *parent_parsers: argparse.ArgumentParser
) -> argparse.ArgumentParser:
    # Delete Reference.
    parser = subparsers.add_parser(
        "delete-ref",
        parents=parent_parsers,
        help="Delete a reference in database.",
    )
    return subparsers, parser


def create_import_anno(
    subparsers: argparse._SubParsersAction, *parent_parsers: argparse.ArgumentParser
) -> argparse.ArgumentParser:

    # annotate parser
    parser = subparsers.add_parser(
        "import-ann",
        parents=parent_parsers,
        help="Import annotated variant from the SnpEff tool (please see readme.md)",
    )
    parser.add_argument(
        "--sonar-hash",
        help="The .sonar_hash file (generate from match command with vcf format).",
        type=str,
        metavar="FILE",
    )
    parser.add_argument(
        "--ann-input",
        help="tab-delimited file (please see readme.md)",
        type=str,
        metavar="FILE",
    )
    parser.add_argument(
        "--sample-file",
        metavar="FILE",
        help="file containing pair of annotated file path and .snoar_hash path",
        type=str,
        nargs="+",
        default=[],
    )
    return subparsers, parser


"""
def main_old(args):  # noqa: C901
    # process arguments
    # args = parse_args()
    # checkDB connection.
    # set debugging mode
    if hasattr(args, "debug") and args.debug:
        debug = True
    else:
        debug = False

    # with sonarDBManager(debug=debug) as dbm:
    #    logging.info("CHECK DB: Connected successfully!")

    if not hasattr(args, "db"):  # or args.db:
        LOGGER.warning("If NO -db is given, Tool will use variables from .env file.")
    #    if args.tool != "setup" and args.db is not None and not os.path.isfile(args.db):
    #        sys.exit("input error: database does not exist.")

    # tool procedures

    sonarBasics.setup_db(args.db,  args.default_props, reference_gb=args.gbk, debug=debug)

    if args.tool == "db-upgrade":
        print("WARNING: Backup db file before upgrading")
        decision = ""
        while decision not in ("YES", "no"):
            decision = input("Do you really want to perform this action? [YES/no]: ")
        if decision == "YES":
            sonarDBManager.upgrade_db(args.db)
        else:
            LOGGER.info("No operation is performed")
    else:
        with sonarDBManager(args.db, readonly=True) as dbm:
            dbm.check_db_compatibility()

            # check all conditions before continuing
            # check reference
            if hasattr(args, "reference") and args.reference:
                if len(dbm.references) != 0 and args.reference not in [
                    d["accession"] for d in dbm.references
                ]:
                    rows = dbm.references
                    if not rows:
                        print("*** no references ***")
                    else:
                        print("*** Available Reference***")
                        print(tabulate(rows, headers="keys", tablefmt="fancy_grid"))
                    sys.exit(
                        "Input Error: "
                        + str(args.reference)
                        + " is not available in our database."
                    )
    # other than the above
    # import
    if args.tool == "import":
        # Check if only one number is passed
        if args.method == 1:
            LOGGER.info("Method: MAFFT aligner")
        elif args.method == 2:
            LOGGER.info("Method: Parasail aligner")
        else:
            sys.exit("Invalid method. Please choose 1 for MAFFT or 2 for Parasail.")


        sonarBasics.import_data(
            db=args.db,
            fasta=args.fasta,
            csv_files=args.csv,
            tsv_files=args.tsv,
            cols=args.cols,
            cachedir=args.cache,
            autolink=args.auto_link,
            progress=not args.no_progress,
            update=not args.no_update,
            threads=args.threads,
            debug=args.debug,
            reference=args.reference,
            method=args.method
        )


    # delete
    elif args.tool == "delete":
        samples = set([x.strip() for x in args.sample])
        for file in args.sample_file:
            check_file(file)
            with open_file(file, compressed="auto") as handle:
                for line in handle:
                    samples.add(line.strip())
        if len(samples) == 0:
            LOGGER.info("Nothing to delete.")
        else:
            sonarBasics.delete(args.db, *samples, debug=args.debug)

    # restore
    elif args.tool == "restore":
        samples = set([x.strip() for x in args.sample])
        for file in args.sample_file:
            check_file(file)
            with sonarBasics.open_file(file, compressed="auto") as handle:
                for line in handle:
                    samples.add(line.strip())
        if len(samples) == 0:
            LOGGER.info("Nothing to restore.")
        else:
            sonarBasics.restore(
                args.db,
                *samples,
                aligned=args.aligned,
                debug=args.debug,
            )


    # match
    elif args.tool == "match":
        props = {}
        reserved_props = {}

        with sonarDBManager(args.db, readonly=False, debug=args.debug) as dbm:
            for pname in dbm.properties:
                if hasattr(args, pname):
                    props[pname] = getattr(args, pname)
            if args.with_sublineage:
                if args.with_sublineage in dbm.properties:
                    reserved_props["with_sublineage"] = args.with_sublineage
                else:
                    sys.exit(
                        "Input Error: "
                        + args.with_sublineage
                        + " is mismatch to the available properties"
                    )
            # check column output and property name
            if args.out_column != "all":
                out_column = args.out_column.strip()
                out_column_list = out_column.split(",")
                _all_avi_columns = list(dbm.properties.keys())
                check = all(
                    item in _all_avi_columns + ["NUC_PROFILE", "AA_PROFILE"]
                    for item in out_column_list
                )
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

        # Support file upload
        if args.sample_file:
            for sample_file in args.sample_file:
                check_file(sample_file)
                with open_file(sample_file, compressed="auto") as file:
                    for line in file:
                        reserved_props = sonarBasics.set_key(
                            reserved_props, "sample", line.strip()
                        )
        format = "count" if args.count else args.format
        sonarBasics.match(
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
    # reference
    elif args.tool == "add-ref":
        if args.gbk:
            check_file(args.gbk)
        flag = sonarBasics.add_ref_by_genebank_file(args.db, args.gbk, debug=args.debug)
        if flag == 0:
            LOGGER.info("The reference has been added successfully")
    elif args.tool == "list-ref":
        with sonarDBManager(args.db, debug=debug) as dbm:
            rows = dbm.references
            if not rows:
                print("*** no references ***")
                exit(0)
            print(tabulate(rows, headers="keys", tablefmt="fancy_grid"))
    elif args.tool == "import-ann":
        paired_list = []
        if args.sample_file:
            LOGGER.info("Bulk insert: ")
            for file in args.sample_file:
                with open_file(file, compressed="auto") as f:
                    for line in f:
                        if line.strip() == "":
                            continue
                        ann_input, sonar_hash = line.split()
                        check_file(ann_input)
                        check_file(sonar_hash)
                        paired_list.append((ann_input, sonar_hash))
        else:
            if args.ann_input is None or args.sonar_hash is None:
                LOGGER.error("Both --ann-input and --sonar-hash are required.")
                sys.exit(1)
            check_file(args.ann_input)
            check_file(args.sonar_hash)
            paired_list.append((args.ann_input, args.sonar_hash))
        sonarBasics.process_annotation(args.db, paired_list)
        pass

    # optimize
    if args.tool == "optimize":
        with sonarDBManager(args.db, debug=args.debug) as dbm:
            dbm.optimize(args.db)

    # dev
    if args.tool == "dev":
        LOGGER.info("***Dev. mode***")
        if args.up_vartype:
            fix_annotation(args.db, debug=args.debug)
        elif args.up_pre_ref:
            fix_pre_ref(args.db, debug=args.debug)
        elif args.up_ele_nt:
            fix_element_id_NT(args.db, debug=args.debug)
        else:
            test_align_mafft()
        LOGGER.info("***Done...***")
    # Finished successfully
    return 0
"""


def run():
    # print(sys.argv[1:])
    parsed_args = parse_args(sys.argv[1:])
    main(parsed_args)


def handle_setup(args: argparse.Namespace):
    """
    Handle database setup.

    Args:
        args (argparse.Namespace): Parsed command line arguments.

    Raises:
        FileNotFoundError: If the specified GenBank file is not found.
    """
    if args.gbk:
        check_file(args.gbk)
    sonarUtils.setup_db(
        db_url=args.db, default_props=args.default_props, reference_gb=args.gbk
    )


def handle_db_upgrade(args: argparse.Namespace):
    """
    Handle database upgrade, prompting the user to confirm the action.

    Args:
        args (argparse.Namespace): Parsed command line arguments.
    """
    LOGGER.warning("Backup your database before upgrading")
    decision = ""
    while decision not in ("YES", "no"):
        decision = input("Do you really want to perform this action? [YES/no]: ")
    if decision == "YES":
        sonarDBManager.upgrade_db(args.db)
    else:
        LOGGER.info("No operation is performed")


def handle_import(args: argparse.Namespace):
    """
    Handle data import.

    Args:
        args (argparse.Namespace): Parsed command line arguments.
    """

    if args.method == 1:
        LOGGER.info("Method: MAFFT aligner")
    elif args.method == 2:
        LOGGER.info("Method: Parasail aligner")
    else:
        print("Invalid method. Please choose 1 for MAFFT or 2 for Parasail.")
        exit(1)

    sonarUtils.import_data(
        db=args.db,
        fasta=args.fasta,
        csv_files=args.csv,
        tsv_files=args.tsv,
        prop_links=args.cols,
        cachedir=args.cache,
        autolink=args.auto_link,
        auto_anno=args.auto_anno,
        progress=not args.no_progress,
        update=not args.no_update,
        threads=args.threads,
        quiet=args.debug,
        reference=args.reference,
        method=args.method,
    )


def handle_list_ref(args: argparse.Namespace):
    with sonarDBManager(args.db, debug=args.debug) as dbm:
        rows = dbm.references
        if not rows:
            print("*** no references ***")
            exit(0)
        print(tabulate(rows, headers="keys", tablefmt="fancy_grid"))


def handle_delete_ref(args: argparse.Namespace):
    # del ref
    if args.reference is None:
        print("No reference is given, please add '--reference' ")
        exit(1)

    LOGGER.warning(
        f"When the {args.reference} is removed, all samples with this reference will also be removed."
    )
    LOGGER.warning(
        "If you need to import data again with new database, you might have to use a new cache directory."
    )
    decision = ""
    while decision not in ("YES", "NO"):
        decision = input("Do you really want to delete this reference? [YES/no]: ")
        decision = decision.upper()

    if decision.upper() == "YES":
        sonarUtils.del_ref(args.db, args.reference, args.debug)
        LOGGER.info("Reference deleted.")
    else:
        LOGGER.info("Reference not deleted.")


def handle_add_ref(args: argparse.Namespace):
    if args.gbk:
        check_file(args.gbk)
    flag = sonarUtils.add_ref_by_genebank_file(args.db, args.gbk, debug=args.debug)
    if flag == 0:
        LOGGER.info("The reference has been added successfully.")


def handle_list_prop(args: argparse.Namespace):
    """
    Handle listing properties from the database.
    This function retrieves all properties stored in the database, sorts them by
    name, and formats the output as a table. The table includes columns such as
    name, argument, subject, description, data type, query type, and standard value.
    The formatted table is then printed to the console.

    Args:
        args (argparse.Namespace): Parsed command line arguments.
    """
    with sonarDBManager(args.db) as db_manager:
        if not db_manager.properties:
            print("*** no properties ***")
        else:
            cols = [
                "name",
                "argument",
                "subject",
                "description",
                "data type",
                "query type",
                "standard value",
            ]
            rows = []
            for prop in sorted(db_manager.properties.keys()):
                dt = (
                    db_manager.properties[prop]["datatype"]
                    if db_manager.properties[prop]["datatype"] != "float"
                    else "decimal number"
                )
                rows.append([])
                rows[-1].append(prop)
                rows[-1].append("--" + prop)
                rows[-1].append("sample")
                rows[-1].append(
                    fill(db_manager.properties[prop]["description"], width=25)
                )
                rows[-1].append(dt)
                rows[-1].append(db_manager.properties[prop]["querytype"])
                rows[-1].append(db_manager.properties[prop]["standard"])

            print(tabulate(rows, headers=cols, tablefmt="fancy_grid"))


def handle_add_prop(args: argparse.Namespace):
    """
    Handle adding a new property to the database.

    Args:
        args (argparse.Namespace): Parsed command line arguments.
    """
    with sonarDBManager(args.db, readonly=False) as db_manager:
        if args.qtype is None:
            if args.dtype == "integer":
                args.qtype = "numeric"
            elif args.dtype == "float":
                args.qtype = "float"
            elif args.dtype == "text":
                args.qtype = "text"
            elif args.dtype == "date":
                args.qtype = "date"
            elif args.dtype == "zip":
                args.qtype = "zip"
            elif args.dtype == "pango":
                args.dtype = "text"
                args.qtype = "pango"
        db_manager.add_property(
            args.name,
            args.dtype,
            args.qtype,
            args.descr,
            args.subject,
            args.default,
        )
    LOGGER.info("Inserted successfully: %s", args.name)


def handle_delete_prop(args: argparse.Namespace):
    """
    Handle deleting an existing property from the database.

    This function removes a specified property from the database. If the 'force'
    option is not set, the user is prompted to confirm the deletion, especially
    when there are samples with non-default values for the property.

    Args:
    args (argparse.Namespace): Parsed command line arguments containing the
    property name to be deleted and the 'force' flag.

    Raises:
    SystemExit: If the specified property name is not found in the database.
    """
    with sonarDBManager(args.db, readonly=False) as db_manager:
        if args.name not in db_manager.properties:
            LOGGER.error("Unknown property.")
            sys.exit(1)

        non_default_values_count = db_manager.count_property(
            args.name, ignore_standard=True
        )

        if args.force:
            decision = "yes"
        else:
            LOGGER.warning(
                f"There are {non_default_values_count} samples with non-default values for this property."
            )
            decision = ""
            while decision not in ("yes", "no"):
                decision = input(
                    "Do you really want to delete this property? [YES/no]: "
                ).lower()

        if decision.lower() == "yes":
            db_manager.delete_property(args.name)
            LOGGER.info("Property is deleted.")
        else:
            LOGGER.info("Property is not deleted.")


def handle_delete(args: argparse.Namespace):
    """
    Handle deleting a sample from the database.

    This function removes specified samples from the database. The samples can be
    provided as command line arguments or within a file. If the 'force' option is
    not set, the user is prompted to confirm the deletion, especially when there
    are samples with non-default values for any property.

    Args:
        args (argparse.Namespace): Parsed command line arguments containing the
                                        sample names to be deleted and the 'force' flag.

    Raises:
        FileNotFoundError: If the specified sample file is not found.
        SystemExit: If none of the specified samples are found in the database.
    """
    samples = set([x.strip() for x in args.sample])
    for fname in args.sample_file:
        check_file(fname)
        with sonarBasics.open_file_autodetect(fname) as handle:
            for line in handle:
                samples.add(line.strip())
    if len(samples) == 0:
        LOGGER.info("Nothing to delete.")
    else:
        sonarUtils.delete_sample(args.db, samples)


def handle_restore(args: argparse.Namespace):
    """
    Handle restoring genome sequences from the database.

    This function retrieves specified genome sequences from the database and
    writes them to an output file. The samples can be provided as command line
    arguments or within a file. Optionally, the output can contain aligned
    sequences.

    Args:
        args (argparse.Namespace): Parsed command line arguments containing the
                                        sample names to be restored and optional flags
                                        such as 'aligned' and 'out'.
    Raises:
        FileNotFoundError: If the specified sample file is not found.
    """

    samples = set([x.strip() for x in args.sample])
    for file in args.sample_file:
        check_file(file)
        with sonarBasics.open_file_autodetect(file) as handle:
            for line in handle:
                samples.add(line.strip())
    if len(samples) == 0:
        LOGGER.info("Nothing to restore.")
        # sys.exit(0)
        return
    if args.reference is None:
        LOGGER.info("No reference is given.")

    sonarUtils.restore_seq(
        args.db,
        samples,
        aligned=args.aligned,
        outfile=args.out,
    )

    # def handle_update_pangolin(args: argparse.Namespace):
    """
    Handle update pangolin information.

    This function updates the parent-child relationship of pangolin lineages
    stored in the database by obtaining the latest lineage data.

    Args:
        args (argparse.Namespace): Parsed command line arguments.

    Raises:
        FileNotFoundError: If any required files are not found.
    """
    """
    with sonarLinmgr() as lineage_manager:
        lineage_data = lineage_manager.update_lineage_data()

    with sonarDBManager(args.db, readonly=False) as db_manager:
        db_manager.add_update_lineage(lineage_data)
    """


def handle_info(args: argparse.Namespace):
    """
    Handle displaying database information.

    This function retrieves and displays the database information, including
    various statistics and metadata about the stored data.

    Args:
        args (argparse.Namespace): Parsed command line arguments.

    Raises:
        FileNotFoundError: If the database file is not found.
    """
    sonarUtils.show_db_info(args.db, args.detailed)


def handle_match(args: argparse.Namespace):
    """
    Handle profile and property matching.

    This function matches samples based on their properties and a given profile.
    The samples can be provided as command line arguments or within a file.
    The output can be customized by selecting specific output columns.

    Args:
        args (argparse.Namespace): Parsed command line arguments containing the
                                        profile, sample names, output format, and other
                                        optional flags.

    Raises:
        FileNotFoundError: If any required files are not found.
        SystemExit: If any unknown output columns are selected.
    """
    properties = {}
    with sonarDBManager(args.db, readonly=False) as db_manager:
        for property_name in db_manager.properties:
            if hasattr(args, property_name):
                properties[property_name] = getattr(args, property_name)

        # Check output column names and property names
        if len(args.out_cols) > 0:
            if all(item in db_manager.properties for item in args.out_cols):
                # sample.name is fixed for output
                args.out_cols = ["SAMPLE_NAME"] + args.out_cols
            else:
                LOGGER.error(
                    "Unknown output column(s) selected. Please select from: "
                    + ", ".join(db_manager.properties)
                )
                sys.exit(1)

    # Sample name handling
    samples = set(args.sample)
    if args.sample_file:
        for sample_file in args.sample_file:
            check_file(sample_file)
            with sonarBasics.open_file_autodetect(sample_file) as file:
                for line in file:
                    samples.add(line.strip())

    # Set output format
    output_format = "count" if args.count else args.format

    # Perform matching
    sonarUtils.match(
        db=args.db,
        profiles=args.profile,
        reference=args.reference,
        samples=samples,
        properties=properties,
        outfile=args.out,
        output_column=args.out_cols,
        format=output_format,
        showNX=args.showNX,
        frameshifts_only=args.frameshifts_only,
    )


def handle_import_ann(args: argparse.Namespace):
    paired_list = []
    if args.sample_file:
        LOGGER.info("Bulk insert: ")
        for file in args.sample_file:
            with sonarBasics.open_file_autodetect(file) as f:
                for line in f:
                    if line.strip() == "":
                        continue
                    ann_input, sonar_hash = line.split()
                    check_file(ann_input)
                    check_file(sonar_hash)
                    paired_list.append((ann_input, sonar_hash))
    else:
        if args.ann_input is None or args.sonar_hash is None:
            LOGGER.error("Both --ann-input and --sonar-hash are required.")
            sys.exit(1)
        check_file(args.ann_input)
        check_file(args.sonar_hash)
        paired_list.append((args.ann_input, args.sonar_hash))
    sonarUtils.process_annotation(args.db, paired_list)


def handle_optimize(args: argparse.Namespace):
    """
    Handle database optimization.

    This function optimizes the database by performing operations that
    improve the performance and reduce the storage space.

    Args:
        arguments (argparse.Namespace): Parsed command line arguments.

    Raises:
        FileNotFoundError: If the database file is not found.
    """
    with sonarDBManager(args.db) as db_manager:
        db_manager.optimize()


def handle_direct_query(args: argparse.Namespace):
    """
    Handle read-only SQLite queries.

    This function allows the user to execute read-only SQLite queries
    directly on the database. The results can be written to an output file.

    Args:
        arguments (argparse.Namespace): Parsed command line arguments containing
                                        the SQL query and optional output file.

    Raises:
        FileNotFoundError: If the database file is not found.
    """
    if len(args.sql) > 1 and (
        (args.sql.startswith('"') and args.sql.endswith('"'))
        or (args.sql.startswith("'") and args.sql.endswith("'"))
    ):
        sql = args.sql[1:-1]
    else:
        sql = args.sql
    sonarUtils.direct_query(args.db, query=sql, outfile=args.out)


def execute_commands(args):  # noqa: C901
    """
    Execute the appropriate function based on the provided command.
    This function determines which command was provided as an argument and
    calls the corresponding function to handle the command. It also ensures
    the database compatibility before executing the command.

    Args:
        args (argparse.Namespace): Parsed command line arguments.
    """
    if args.command == "setup":
        handle_setup(args)
    elif args.command == "db-upgrade":
        handle_db_upgrade(args)
    else:
        with sonarDBManager(args.db, readonly=True) as db_manager:
            db_manager.check_db_compatibility()

    if args.command == "import":
        handle_import(args)
    elif args.command == "import-ann":
        handle_import_ann(args)
    elif args.command == "list-ref":
        handle_list_ref(args)
    elif args.command == "add-ref":
        handle_add_ref(args)
    elif args.command == "delete-ref":
        handle_delete_ref(args)
    elif args.command == "list-prop":
        handle_list_prop(args)
    elif args.command == "add-prop":
        handle_add_prop(args)
    elif args.command == "delete-prop":
        handle_delete_prop(args)
    elif args.command == "delete":
        handle_delete(args)
    elif args.command == "restore":
        handle_restore(args)
    elif args.command == "info":
        handle_info(args)

    # elif args.command == "update-lineages":
    #    handle_update_pangolin(args)

    elif args.command == "match":
        handle_match(args)
    elif args.command == "optimize":

        handle_optimize(args)
    elif args.command == "direct-query":
        handle_direct_query(args)

    elif args.command == "dev":
        LOGGER.info("***Dev. mode***")
        if args.up_vartype:
            fix_annotation(args.db, debug=args.debug)
        elif args.up_pre_ref:
            fix_pre_ref(args.db, debug=args.debug)
        elif args.up_ele_nt:
            fix_element_id_NT(args.db, debug=args.debug)
        else:
            test_align_mafft()
        LOGGER.info("***Done...***")


def main(args: Optional[argparse.Namespace] = None) -> int:
    """
    The main function that handles the execution of different commands.

    Args:
        args (Optional[argparse.Namespace]): Namespace containing parsed command-line arguments.
            If None, the function will parse the arguments itself.

    Returns:
        int: Returns 0 if finished successfully.
    """
    # process arguments
    if not args:
        args = parse_args(sys.argv[1:])

    # Set debugging mode
    if hasattr(args, "debug") and args.debug:
        debug = True
    else:
        debug = False
        args.debug = False

    LoggingConfigurator(debug=debug)

    # Check database
    if not hasattr(args, "db"):  # or args.db:
        LOGGER.warning(
            "'-db' argument was not provided, the tool will use information from a '.env' file"
        )
        args.db = DB_URL

    # other commands
    execute_commands(args)

    # Finished successfully
    return 0


if __name__ == "__main__":
    run()
