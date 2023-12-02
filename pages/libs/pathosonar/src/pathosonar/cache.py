#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# author: Stephan Fuchs (Robert Koch Institute, MF1, fuchss@rki.de)

import base64
from collections import defaultdict
import hashlib
import logging
import os
import pickle
import pprint
import re
import shutil
import sys
import traceback
from typing import Any
from typing import Dict
from typing import Iterator
from typing import Optional
from typing import Union

from mpire import WorkerPool
import pandas as pd
from tqdm import tqdm

from .align import sonarAligner
from .annotation import Annotator
from .annotation import export_vcf_SonarCMD
from .annotation import import_annvcf_SonarCMD
from .basics import sonarBasics
from .config import ANNO_TOOL_PATH
from .config import DB_URL
from .config import SNPSIFT_TOOL_PATH
from .config import TMP_CACHE
from .config import VCF_ONEPERLINE_PATH
from .dbm import sonarDBManager
from .logging import LoggingConfigurator
from .utils_1 import get_filename_sonarhash

# from .basics import sonarBasics

pp = pprint.PrettyPrinter(indent=4)
# Initialize logger
LOGGER = LoggingConfigurator.get_logger()


class sonarCache:
    """ """

    def __init__(
        self,
        db: Optional[str] = None,
        outdir: Optional[str] = None,
        refacc: Optional[str] = None,
        logfile: Optional[str] = None,
        allow_updates: bool = True,
        ignore_errors: bool = False,
        temp: bool = False,
        debug: bool = False,
        disable_progress: bool = False,
    ):
        """
        Initialize the sonarCache object.

        Args:
            db (str): The database to import.
            outdir (str): The output directory to cache data.
            refacc (str): The reference accession.
            logfile (str): The log file to use.
            allow_updates (bool): Whether to allow updates or not.
            ignore_errors (bool): Whether to skip import errors and keep on going.
            temp (bool): Whether to set cache dir temporary or not.
            disable_progress (bool): Whether to disable progress display or not.
        """

        if db is not None:
            self.db = db
        elif db is None and DB_URL is not None:
            # logging.warning("No --db is given, MPXSonar use variables from .env file.")
            self.db = DB_URL
        else:
            LOGGER.error("NO database info. is given.")
            sys.exit(1)

        self.allow_updates = allow_updates
        self.debug = debug
        self.refacc = refacc
        self.temp = temp
        self.ignore_errors = ignore_errors
        self.disable_progress = disable_progress

        with sonarDBManager(self.db, debug=self.debug) as dbm:
            self.refmols = dbm.get_molecule_data(
                "`molecule.accession`",
                "`molecule.id`",
                "`molecule.standard`",
                "`translation.id`",
                reference_accession=self.refacc,
            )
            if not self.refmols:
                logging.info(f"Cannot find reference: {self.refacc}")
                sys.exit()
            if self.debug:
                logging.info(f"Init refmols: {self.refmols}")

            """
            self.default_refmol_acc = [
                x for x in self.refmols if self.refmols[x]["molecule.standard"] == 1
            ][0]
            self.default_refmol_id = [
                x for x in self.refmols if self.refmols[x]["molecule.id"] == 1
            ][0]
            self.sources = {
                x["molecule.accession"]: dbm.get_source(x["molecule.id"])
                for x in self.refmols.values()
            }
            """
            self.default_refmol_acc = [
                x for x in self.refmols if self.refmols[x]["molecule.standard"] == 1
            ][0]

            self.default_refmol_id = [
                self.refmols[x]["molecule.id"] for x in self.refmols
            ][0]

            self.sources = {
                x["molecule.accession"]: dbm.get_source(x["molecule.id"])
                for x in self.refmols.values()
            }
            self.properties = dbm.properties

        self._propregex = re.compile(
            r"\[(" + "|".join(self.properties.keys()) + r")=([^\[\]=]+)\]"
        )
        self._molregex = re.compile(r"\[molecule=([^\[\]=]+)\]")

        self.basedir = TMP_CACHE if not outdir else os.path.abspath(outdir)

        if not os.path.exists(self.basedir):
            os.makedirs(self.basedir)

        self.logfile = (
            open(os.path.join(self.basedir, logfile), "a+") if logfile else None
        )
        self.smk_config = os.path.join(self.basedir, "config.yaml")
        self.sample_dir = os.path.join(self.basedir, "samples")
        self.seq_dir = os.path.join(self.basedir, "seq")
        self.algn_dir = os.path.join(self.basedir, "algn")
        self.var_dir = os.path.join(self.basedir, "var")
        self.ref_dir = os.path.join(self.basedir, "ref")
        self.error_dir = os.path.join(self.basedir, "error")
        self.anno_dir = os.path.join(self.basedir, "anno")

        os.makedirs(self.basedir, exist_ok=True)
        os.makedirs(self.seq_dir, exist_ok=True)
        os.makedirs(self.ref_dir, exist_ok=True)
        # os.makedirs(self.algn_dir, exist_ok=True)
        os.makedirs(self.var_dir, exist_ok=True)
        os.makedirs(self.sample_dir, exist_ok=True)
        os.makedirs(self.error_dir, exist_ok=True)
        os.makedirs(self.anno_dir, exist_ok=True)

        self._samplefiles = set()
        self._samplefiles_to_profile = set()
        self._refs = set()
        self._lifts = set()
        self._cds = set()
        self._tt = set()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if os.path.isdir(self.basedir) and self.temp:
            shutil.rmtree(self.basedir)
        if self.logfile:
            self.logfile.close()

    @staticmethod
    def slugify(string):
        return (
            base64.urlsafe_b64encode(string.encode("UTF-8")).decode("UTF-8").rstrip("=")
        )

    # Do we need this function?
    # @staticmethod
    # def deslugify(string):
    #    while len(string) % 3 != 0:
    #        string += "="
    #    return base64.urlsafe_b64decode(string).decode("utf-8")

    def log(self, msg, die=False, errtype="error"):
        if self.logfile:
            self.logfile.write(msg + "\n")
        elif not die:
            sys.stderr.write(msg + "\n")
        else:
            exit(errtype + ": " + msg)

    @staticmethod
    def write_pickle(fname, data):
        with open(fname, "wb") as handle:
            pickle.dump(data, handle)

    @staticmethod
    def read_pickle(fname):
        with open(fname, "rb") as handle:
            return pickle.load(handle, encoding="bytes")

    # Do we need this function?
    # @staticmethod
    # def pickle_collision(fname, data):
    #     if os.path.isfile(fname) and load_pickle(fname) != data:
    #        return True
    #    return False

    @staticmethod
    def file_collision(fname, data):
        with open(fname, "r") as handle:
            if handle.read() != data:
                return True
        return False

    def get_cds_fname(self, refid):
        return os.path.join(self.ref_dir, str(refid) + ".lcds")

    def get_seq_fname(self, seqhash):
        fn = self.slugify(seqhash)
        return os.path.join(self.seq_dir, fn[:2], fn + ".seq")

    def get_ref_fname(self, refid):
        return os.path.join(self.ref_dir, str(refid) + ".seq")

    def get_lift_fname(self, refid):
        return os.path.join(self.ref_dir, str(refid) + ".lift")

    def get_tt_fname(self, refid):
        return os.path.join(self.ref_dir, str(refid) + ".tt")

    def get_algn_fname(self, seqhash):
        fn = self.slugify(seqhash)
        return os.path.join(self.algn_dir, fn[:2], fn + ".algn")

    def get_var_fname(self, seqhash):
        fn = self.slugify(seqhash)
        return os.path.join(self.var_dir, fn[:2], fn + ".var")

    def get_sample_fname(self, sample_name):
        fn = self.slugify(hashlib.sha1(sample_name.encode("utf-8")).hexdigest())
        return os.path.join(self.sample_dir, fn[:2], fn + ".sample")

    def get_vcf_fname(self, sample_name):
        fn = self.slugify(hashlib.sha1(sample_name.encode("utf-8")).hexdigest())
        return os.path.join(self.anno_dir, fn[:2], fn + ".vcf")

    def get_anno_vcf_fname(self, sample_name):
        fn = self.slugify(hashlib.sha1(sample_name.encode("utf-8")).hexdigest())
        return os.path.join(self.anno_dir, fn[:2], fn + ".ann.vcf")

    def get_anno_tsv_fname(self, sample_name):
        fn = self.slugify(hashlib.sha1(sample_name.encode("utf-8")).hexdigest())
        return os.path.join(self.anno_dir, fn[:2], fn + ".ann.tsv")

    def cache_sample(
        self,
        name,
        sampleid,
        seqhash,
        header,
        refmol,
        refmolid,
        source_acc,
        sourceid,
        translation_id,
        algnid,
        seqfile,
        mafft_seqfile,
        vcffile,
        anno_vcf_file,
        anno_tsv_file,
        reffile,
        ttfile,
        algnfile,
        varfile,
        liftfile,
        cdsfile,
        properties,
    ):
        """
        The function takes in a bunch of arguments and returns a filename.
        :return: A list of dictionaries. Each dictionary contains the information for a single sample.
        """

        data = {
            "name": name,
            "sampleid": sampleid,
            "refmol": refmol,  # from molecule table, moleculd accession
            "refmolid": refmolid,  # from molecule table, moleculd id
            "source_acc": source_acc,
            "sourceid": sourceid,
            "translationid": translation_id,
            "algnid": algnid,
            "header": header,
            "seqhash": seqhash,
            "seq_file": seqfile,
            "mafft_seqfile": mafft_seqfile,
            "vcffile": vcffile,
            "anno_vcf_file": anno_vcf_file,
            "anno_tsv_file": anno_tsv_file,
            "ref_file": reffile,
            "tt_file": ttfile,
            "algn_file": algnfile,
            "var_file": varfile,
            "lift_file": liftfile,
            "cds_file": cdsfile,
            "properties": properties,
        }
        fname = self.get_sample_fname(name)  # return fname with full path

        self.log("Get:" + fname)

        try:
            self.write_pickle(fname, data)
        except OSError:
            os.makedirs(os.path.dirname(fname), exist_ok=True)
            self.write_pickle(fname, data)
        # Keeps Full path of each sample.
        self._samplefiles.add(fname)
        if algnid is None:
            self._samplefiles_to_profile.add(fname)
        return fname

    def iter_samples(self):
        for fname in self._samplefiles:
            yield self.read_pickle(fname)

    def cache_sequence(self, seqhash, sequence):

        fname = self.get_seq_fname(seqhash)
        if os.path.isfile(fname):
            if self.file_collision(fname, sequence):
                sys.exit(
                    "seqhash collision: sequences differ for seqhash " + seqhash + "."
                )
        else:
            try:
                with open(fname, "w") as handle:
                    handle.write(sequence)
            except OSError:
                os.makedirs(os.path.dirname(fname), exist_ok=True)
                with open(fname, "w") as handle:
                    handle.write(sequence)
        return fname

    def cache_reference(self, refid, sequence):
        fname = self.get_ref_fname(refid)
        if refid not in self._refs:
            with open(fname, "w") as handle:
                handle.write(sequence)
            self._refs.add(refid)
        return fname

    def cache_seq_mafftinput(self, refid, ref_sequence, seqhash, qry_sequence):
        """
        This function create fasta file which contains
        only ref and query seq. The file will be used for MAFFT input.
        """
        # Get fname (.seq)
        fname = self.get_seq_fname(seqhash)
        fname = fname + ".fasta"  # (.seq.fasta)

        try:
            os.makedirs(os.path.dirname(fname), exist_ok=True)
            with open(fname, "w") as handle:
                handle.write(">" + refid + "\n")
                handle.write(ref_sequence + "\n")
                handle.write(">" + seqhash + "\n")
                handle.write(qry_sequence + "\n")
        except OSError as e:
            LOGGER.error(f"An error occurred: {e}")
            sys.exit(1)
        return fname

    def cache_translation_table(self, translation_id, dbm):
        """
        If the translation table
        is not in the cache, it is retrieved from the database and written to a file

        :param translation_id: The id of the translation table
        :param dbm: the database manager
        :return: A file name.
        """
        fname = self.get_tt_fname(translation_id)  # write under /cache/ref/
        if translation_id not in self._tt:
            self.write_pickle(fname, dbm.get_translation_dict(translation_id))
            self._tt.add(translation_id)
        return fname

    def cache_cds(self, refid, refmol_acc):
        """
                The function takes in a reference id, a reference molecule accession number,
                and a reference sequence. It then checks to see if the reference molecule accession number is in the set of molecules that
                have been cached. If it is not, it iterates through all of the coding sequences for that molecule and creates a
                dataframe for each one.
        .
                It then saves the dataframe to a pickle file and adds the reference molecule accession number to
                the set of molecules that have been cached.
                It then returns the name of the pickle file
        """
        fname = self.get_cds_fname(refid)
        if refmol_acc not in self._cds:
            rows = []
            cols = ["elemid", "pos", "end"]
            for cds in self.iter_cds(refmol_acc):
                elemid = cds["id"]
                coords = []
                for rng in cds["ranges"]:
                    coords.extend(list(rng))
                for coord in coords:
                    rows.append([elemid, coord, 0])
                # rows[-1][2] = 1
                # print(rows)
                df = pd.DataFrame.from_records(rows, columns=cols, coerce_float=False)
                df.to_pickle(fname)
                if self.debug:
                    df.to_csv(fname + ".csv")
            self._cds.add(refmol_acc)
        return fname

    def cache_lift(self, refid, refmol_acc, sequence):
        """
        The function takes in a reference id, a reference molecule accession number,
        and a reference sequence. It then checks to see if the reference molecule accession number is in the set of molecules that
        have been cached. If it is not, it iterates through all of the coding sequences for that molecule and creates a
        dataframe for each one.
        It then saves the dataframe to a pickle file and adds the reference molecule accession number to
        the set of molecules that have been cached.
        It then returns the name of the pickle file.
        """
        fname = self.get_lift_fname(refid)
        rows = []
        if refmol_acc not in self._lifts:
            cols = [
                "elemid",
                "nucPos1",
                "nucPos2",
                "nucPos3",
                "ref1",
                "ref2",
                "ref3",
                "alt1",
                "alt2",
                "alt3",
                "symbol",
                "accession",
                "aaPos",
                "aa",
            ]
            # if there is no cds, the lift file will not be generated
            for cds in self.iter_cds(refmol_acc):
                elemid = cds["id"]
                symbol = cds["symbol"]
                accession = cds["accession"]
                seq = cds["sequence"] + "*"
                codon = 0
                i = 0
                coords = []
                for rng in cds["ranges"]:
                    coords.extend(list(rng))
                while len(coords) % 3 != 0:
                    coords.append("")
                coords_len = len(coords)
                while len(seq) < coords_len / 3:
                    seq += "-"
                while len(sequence) < coords_len:
                    sequence += "-"
                for i, coord in enumerate(
                    [coords[x : x + 3] for x in range(0, len(coords), 3)]
                ):
                    codon = [sequence[coord[0]], sequence[coord[1]], sequence[coord[2]]]
                    rows.append(
                        [elemid]
                        + coord
                        + codon
                        + codon
                        + [symbol, accession, i, seq[i].strip()]
                    )
            df = pd.DataFrame.from_records(rows, columns=cols, coerce_float=False)
            df = df.reindex(df.columns.tolist(), axis=1)
            df.to_pickle(fname)
            if self.debug:
                df.to_csv(fname + ".csv")
            self._lifts.add(refmol_acc)

        return fname

    def process_fasta_entry(self, header: str, seq: str) -> Dict[str, Union[str, int]]:
        """
        Formulate a data dict.

        Return:
            Dict
                example:
                {'name': 'OQ331004.1', 'header': 'OQ331004.1 Monkeypox virus isolate Monkeypox virus/Human/USA/CA-LACPHL-MA00393/2022,
                partial genome', 'seqhash': 'Bjhx5hv8G4m6v8kpwt4isQ4J6TQ', 'sequence': 'TACTGAAGAAW',
                'refmol': 'NC_063383.1', <-- molecule accession
                'refmolid': 1,  <-- molecule ID
                'translation_id': 1,
                'properties': {}}
        """
        try:
            sample_id = header.replace("\t", " ").replace("|", " ").split(" ")[0]
        except AttributeError:
            # Handle the 'NoneType' object has no attribute 'replace' error
            LOGGER.error("Invalid FASTA format")
            sys.exit(1)
        except Exception as e:
            LOGGER.error(f"An error occurred: {e}")
            sys.exit(1)

        refmol = self.get_refmol(header)
        if not refmol:
            sys.exit(
                "input error: "
                + sample_id
                + " refers to an unknown reference molecule ("
                + self._molregex.search(header)
                + ")."
            )
        seq = sonarBasics.harmonize_seq(seq)
        seqhash = sonarBasics.hash_seq(seq)
        refmolid = self.refmols[refmol]["molecule.id"]

        return {
            "name": sample_id,
            "header": header,
            "seqhash": seqhash,
            "sequence": seq,
            "refmol": refmol,
            "refmolid": refmolid,
            "translation_id": self.refmols[refmol]["translation.id"],
            "properties": self.get_properties(header),
        }

    def iter_fasta(self, *fnames: str) -> Iterator[Dict[str, Union[str, int]]]:
        """
        This function iterates over the fasta files and yield a dict of selected reference and
        each sequence.

        """
        for fname in fnames:
            with sonarBasics.open_file_autodetect(fname) as handle, tqdm(
                desc="processing " + fname + "...",
                total=os.path.getsize(fname),
                unit="bytes",
                unit_scale=True,
                bar_format="{desc} {percentage:3.0f}% [{n_fmt}/{total_fmt}, {elapsed}<{remaining}, {rate_fmt}{postfix}]",
                disable=self.disable_progress,
            ) as pbar:
                seq = []
                header = None
                for line in handle:
                    pbar.update(len(line))
                    line = line.strip()
                    if line.startswith(">"):
                        if seq:
                            yield self.process_fasta_entry(header, "".join(seq))
                            seq = []
                        header = line[1:]
                    else:
                        seq.append(line)
                if seq:
                    yield self.process_fasta_entry(header, "".join(seq))

    def get_refmol(self, fasta_header):
        """

        return:
            None: if cannot find mol_id from the header
        """
        mol = self._molregex.search(fasta_header)
        if not mol:
            try:
                print(f"Using refmol_acc: {self.refmols[mol]['accession']}")
                return self.refmols[mol]["accession"]
            except Exception:
                None
        return self.default_refmol_acc

    def get_refseq(self, refmol_acc):
        try:
            return self.sources[refmol_acc]["sequence"]
        except Exception:
            return None

    def iter_cds(self, refmol_acc):
        cds = {}
        prev_elem = None
        with sonarDBManager(self.db, debug=self.debug) as dbm:
            for row in dbm.get_annotation(
                reference_accession=refmol_acc,
                molecule_accession=refmol_acc,
                element_type="cds",
            ):
                if prev_elem is None:
                    prev_elem = row["element.id"]
                elif row["element.id"] != prev_elem:
                    yield cds
                    cds = {}
                    prev_elem = row["element.id"]
                if cds == {}:
                    cds = {
                        "id": row["element.id"],
                        "accession": row["element.accession"],
                        "symbol": row["element.symbol"],
                        "sequence": row["element.sequence"],
                        "ranges": [
                            range(
                                row["elempart.start"],
                                row["elempart.end"],
                                row["elempart.strand"],
                            )
                        ],
                    }
                else:
                    cds["ranges"].append(
                        range(
                            row["elempart.start"],
                            row["elempart.end"],
                            row["elempart.strand"],
                        )
                    )
        if cds:
            yield cds

    def get_refseq_id(self, refmol_acc):
        try:
            return self.sources[refmol_acc]["id"]
        except Exception:
            return None

    def get_refhash(self, refmol_acc: str) -> Optional[str]:
        """
        Get the sequence hash for a given reference molecule accession number.

        Args:
            refmol_acc (str): The reference molecule accession number.

        Returns:
            str/None: The sequence hash if found, or None if not found.
        """
        try:
            if "seqhash" not in self.sources[refmol_acc]:
                self.sources[refmol_acc]["seqhash"] = sonarBasics.hash_seq(
                    self.sources[refmol_acc]["sequence"]
                )
            return self.sources[refmol_acc]["seqhash"]
        except Exception:
            return None

    def get_properties(self, fasta_header):
        return {x.group(1): x.group(2) for x in self._propregex.finditer(fasta_header)}

    def add_fasta(self, *fnames, properties=defaultdict(dict), method=1):  # noqa: C901
        """
        Prepare/Create dict and then write  it ".sample" file (pickle file) to cache directory
        the dict contains all information (e.g., name, algnid, refmol, varfile )
        """
        default_properties = {
            x: self.properties[x]["standard"] for x in self.properties
        }
        failed_list = []
        with sonarDBManager(self.db, debug=self.debug) as dbm:
            for fname in fnames:
                for data in self.iter_fasta(fname):

                    # EDIT: we currently lock the filtering part.
                    # check sequence lenght
                    # if not check_seq_compact(
                    #    self.get_refseq(data["refmol"]), data["sequence"]
                    # ):
                    #    failed_list.append((data["name"], len(data["sequence"])))
                    # log fail samples
                    #    continue

                    # check sample
                    data["sampleid"], seqhash = dbm.get_sample_data(data["name"])
                    source_element = dbm.get_source(data["refmolid"])
                    data["sourceid"] = source_element["id"]
                    data["source_acc"] = source_element["accession"]
                    # check properties
                    if data["sampleid"] is None:
                        props = default_properties.copy()
                        props.update(data["properties"])
                        props.update(properties[data["sampleid"]])
                        data["properties"] = props
                    elif not self.allow_updates:
                        continue
                    else:
                        data["properties"].update(properties[data["sampleid"]])

                    # Check Reference
                    # print("refmol", data)

                    # refseq_id = self.get_refseq_id(data["refmol"])  # this line is from old covsonar
                    # Note Change: IN MPXsonar, we use reference accession (e.g., NC_063383.1)
                    # instead of using ID (e.g., 1) to avoid confusion or altering references across the database.
                    refseq_id = data["refmol"]

                    self.write_checkref_log(data, refseq_id)

                    # Check Alignment
                    data["algnid"] = dbm.get_alignment_id(data["seqhash"], refseq_id)
                    # Write tmp/cache file (e.g., .seq, .ref)
                    data = self.assign_data(data, seqhash, refseq_id, dbm, method)

                    del data["sequence"]
                    self.cache_sample(**data)
        if failed_list:
            self.log(
                "Sample will not be processed due to violate max/min seq lenght rule (+-3%):"
                + str(failed_list),
            )
            LOGGER.warn("Fail max/min seq lenght rule:" + str(failed_list))

    def write_checkref_log(self, data, refseq_id):
        """
        This function linked to the add_fasta()
        """
        if not refseq_id:
            if not self.ignore_errors:
                self.log(
                    "fasta header refers to an unknown refrence ("
                    + data["header"]
                    + ")",
                    True,
                    "input error",
                )
            else:
                self.log(
                    "skipping "
                    + data["name"]
                    + " referring to an unknown reference ("
                    + data["header"]
                    + ")"
                )

    def assign_data(self, data, seqhash, refseq_id, dbm, method):
        """This function linked to the add_fasta

        Create dict to store all related output file.
        and it calls sub function to create all related files.

        Args:
            refseq_id (int): is ID from element table.
            ref_acc (string): is accession from reference table.

        """
        if data["algnid"] is None:
            data["seqfile"] = self.cache_sequence(data["seqhash"], data["sequence"])
            if method == 1:
                data["mafft_seqfile"] = self.cache_seq_mafftinput(
                    refseq_id,
                    self.get_refseq(data["refmol"]),
                    data["seqhash"],
                    data["sequence"],
                )
            else:
                data["mafft_seqfile"] = None
            # TODO: get ref accession number and put into cache_lift
            # to recreate cache directory *(optional task)
            data["reffile"] = self.cache_reference(
                refseq_id, self.get_refseq(data["refmol"])
            )

            data["ttfile"] = self.cache_translation_table(data["translation_id"], dbm)
            data["liftfile"] = self.cache_lift(
                refseq_id, data["refmol"], self.get_refseq(data["refmol"])
            )
            data["cdsfile"] = self.cache_cds(refseq_id, data["refmol"])
            data["algnfile"] = self.get_algn_fname(
                data["seqhash"] + "@" + self.get_refhash(data["refmol"])
            )
            data["varfile"] = self.get_var_fname(
                data["seqhash"] + "@" + self.get_refhash(data["refmol"])
            )

            data["vcffile"] = self.get_vcf_fname(refseq_id + "@" + data["name"])
            data["anno_vcf_file"] = self.get_anno_vcf_fname(
                refseq_id + "@" + data["name"]
            )
            data["anno_tsv_file"] = self.get_anno_tsv_fname(
                refseq_id + "@" + data["name"]
            )

        else:
            # In case, sample is reupload under the same name but changes in fasta
            if data["seqhash"] != seqhash:
                data["seqfile"] = self.cache_sequence(data["seqhash"], data["sequence"])
                if method == 1:
                    data["mafft_seqfile"] = self.cache_seq_mafftinput(
                        refseq_id,
                        self.get_refseq(data["refmol"]),
                        data["seqhash"],
                        data["sequence"],
                    )
                else:
                    data["mafft_seqfile"] = None

                data["vcffile"] = self.get_vcf_fname(refseq_id + "@" + data["name"])
                data["anno_vcf_file"] = self.get_anno_vcf_fname(
                    refseq_id + "@" + data["name"]
                )
                data["anno_tsv_file"] = self.get_anno_tsv_fname(
                    refseq_id + "@" + data["name"]
                )
            else:  # if no changed in sequence. use the existing cache.
                data["seqhash"] = None
                data["seqfile"] = None
                data["mafft_seqfile"] = None
                data["vcffile"] = None
                data["anno_vcf_file"] = None
                data["anno_tsv_file"] = None

            data["reffile"] = None
            data["ttfile"] = None
            data["liftfile"] = None
            data["cdsfile"] = None
            data["algnfile"] = None
            data["varfile"] = None

        return data

    def import_cached_sample(self, **sample_data: Dict[str, Any]) -> None:  # noqa: C901
        list_fail_samples = []
        anno_samples_list = []
        refseqs = {}
        count_sample = 0

        try:
            with sonarDBManager(self.db, readonly=False, debug=self.debug) as dbm:
                # Attempt the database operations
                # nucleotide level import
                var_row_list = []
                if not sample_data["seqhash"] is None:
                    dbm.insert_sample(sample_data["name"], sample_data["seqhash"])
                    algnid = dbm.insert_alignment(
                        sample_data["seqhash"], sample_data["sourceid"]
                    )

                if not sample_data["var_file"] is None:

                    elements_dict = dict()
                    # get element dict
                    elements_rows = dbm.get_elements(
                        molecule_id=sample_data["refmolid"]
                    )
                    # get only neccessary column and add to another dict.
                    for row in elements_rows:
                        elements_dict[row["accession"]] = row["id"]
                    # print(elements_dict)
                    with open(sample_data["var_file"], "r") as handle:
                        for line in handle:
                            if line == "//":
                                break
                            vardat = line.strip("\r\n").split("\t")
                            var_row_list.append(
                                (
                                    elements_dict[vardat[4]],  # element id
                                    vardat[0],  # ref
                                    vardat[3],  # alt
                                    vardat[1],  # start
                                    vardat[2],  # end
                                    vardat[5],  # label
                                    vardat[6],
                                )  # frameshift
                            )
                        if line != "//":
                            sys.exit(
                                "cache error: corrupted file ("
                                + sample_data["var_file"]
                                + ")"
                            )
                # NOTE: we

                if len(var_row_list) > 0:
                    dbm.insert_variant_many(var_row_list, algnid)
                else:
                    LOGGER.info(
                        f"No mutations detected in {sample_data['name']} sample associated with the reference."
                    )

                if not sample_data["seqhash"] is None:
                    # paranoia test
                    paranoid_dict = self.paranoid_check(refseqs, sample_data, dbm)
                    if paranoid_dict:
                        list_fail_samples.append(paranoid_dict)

                count_sample = count_sample + 1

                # "If Dict is Empty", Proceed to Annotation step.
                if not paranoid_dict:
                    anno_samples_list.append(sample_data)

        except Exception as e:
            LOGGER.error("\n------- Fatal Error ---------")
            print(traceback.format_exc())
            print("\nDebugging Information:")
            print(e)
            traceback.print_exc()
            print("\n During insert:")
            pp.pprint(sample_data)
            sys.exit("Unknown import error")

        # time.sleep(random.uniform(0.5, 0.8))

    def import_cached_samples_v2(self, threads, auto_anno=False) -> None:  # noqa: C901
        samples_list = list(self.iter_samples())

        with WorkerPool(n_jobs=threads, start_method="fork") as pool, tqdm(
            position=0,
            leave=True,
            desc="importing samples...",
            total=len(samples_list),
            unit="seqs",
            bar_format="{desc} {percentage:3.0f}% [{n_fmt}/{total_fmt}, {elapsed}<{remaining}, {rate_fmt}{postfix}]",
        ) as pbar:
            for _ in pool.imap_unordered(
                self.import_cached_sample, list(self.iter_samples())
            ):
                pbar.update(1)

    def annotate_sample(self, db_path, sample_data):
        # db_path, sample_data = args
        export_vcf_SonarCMD(
            db_path,
            sample_data["refmol"],
            sample_data["name"],
            sample_data["vcffile"],
        )
        annotator = Annotator(ANNO_TOOL_PATH, SNPSIFT_TOOL_PATH, VCF_ONEPERLINE_PATH)
        annotator.snpeff_annotate(
            sample_data["vcffile"],
            sample_data["anno_vcf_file"],
            sample_data["refmol"],
        )
        annotator.snpeff_transform_output(
            sample_data["anno_vcf_file"], sample_data["anno_tsv_file"]
        )
        import_annvcf_SonarCMD(
            db_path,
            get_filename_sonarhash(sample_data["vcffile"]),
            sample_data["anno_tsv_file"],
        )

    def import_cached_samples(self, threads, auto_anno) -> None:  # noqa: C901
        """
        NOTE: Performance is so slow.
        can we change/edit this process into parallel stlye
        """
        list_fail_samples = []
        anno_samples_list = []
        refseqs = {}
        count_sample = 0
        with sonarDBManager(self.db, readonly=False, debug=self.debug) as dbm:
            for sample_data in tqdm(
                self.iter_samples(),
                total=len(self._samplefiles),
                desc="importing samples...",
                unit="samples",
                bar_format="{desc} {percentage:3.0f}% [{n_fmt}/{total_fmt}, {elapsed}<{remaining}, {rate_fmt}{postfix}]",
                disable=self.disable_progress,
            ):
                # print("\n")
                # print("-----####------ sample_data -----####------")
                # print(sample_data)
                # get the start time
                try:
                    # nucleotide level import
                    var_row_list = []
                    if not sample_data["seqhash"] is None:
                        dbm.insert_sample(sample_data["name"], sample_data["seqhash"])
                        # self.log("sample_data:" + str(sample_data))
                        # sample_data["refmolid"]
                        # print("-----####------ insert_alignment -----####------")
                        # print(sample_data["seqhash"], sample_data["sourceid"])
                        algnid = dbm.insert_alignment(
                            sample_data["seqhash"], sample_data["sourceid"]
                        )
                        # self.log("Get algnid:" + algnid)
                    if not sample_data["var_file"] is None:
                        elements_dict = dict()
                        # get element dict
                        elements_rows = dbm.get_elements(
                            molecule_id=sample_data["refmolid"]
                        )
                        # get only neccessary column and add to another dict.
                        for row in elements_rows:
                            elements_dict[row["accession"]] = row["id"]

                        with open(sample_data["var_file"], "r") as handle:
                            for line in handle:
                                if line == "//":
                                    break
                                vardat = line.strip("\r\n").split("\t")
                                var_row_list.append(
                                    (
                                        elements_dict[vardat[4]],  # element id
                                        vardat[0],  # ref
                                        vardat[3],  # alt
                                        vardat[1],  # start
                                        vardat[2],  # end
                                        vardat[5],  # label
                                        0,  # frameshift (fixed 0, will be removed soon)
                                    )
                                )
                            if line != "//":
                                sys.exit(
                                    "cache error: corrupted file ("
                                    + sample_data["var_file"]
                                    + ")"
                                )
                            if len(var_row_list) > 0:
                                dbm.insert_variant_many(var_row_list, algnid)
                            else:
                                LOGGER.info(
                                    f"No mutations detected in {sample_data['name']} sample associated with the reference."
                                )

                    if not sample_data["seqhash"] is None:
                        # paranoia test
                        paranoid_dict = self.paranoid_check(refseqs, sample_data, dbm)
                        if paranoid_dict:
                            list_fail_samples.append(paranoid_dict)

                        count_sample = count_sample + 1

                        # "If Dict is Empty", Proceed to Annotation step.

                        if not paranoid_dict:
                            anno_samples_list.append(sample_data)

                except Exception as e:
                    LOGGER.error("\n------- Fatal Error ---------")
                    print(traceback.format_exc())
                    print("\nDebugging Information:")
                    print(e)
                    traceback.print_exc()
                    print("\n During insert:")
                    pp.pprint(sample_data)
                    sys.exit("Unknown import error")

        if auto_anno:
            # paired_anno_samples_list = [ {'db_path': self.db, 'sample_data': sample} for sample in anno_samples_list]
            paired_anno_samples_list = list(
                (self.db, sample) for sample in anno_samples_list
            )
            with WorkerPool(n_jobs=threads, start_method="fork") as pool, tqdm(
                position=0,
                leave=True,
                desc="annotate samples...",
                total=len(paired_anno_samples_list),
                unit="samples",
                bar_format="{desc} {percentage:3.0f}% [{n_fmt}/{total_fmt}, {elapsed}<{remaining}, {rate_fmt}{postfix}]",
                disable=self.disable_progress,
            ) as pbar:
                for _ in pool.imap_unordered(
                    self.annotate_sample, paired_anno_samples_list
                ):
                    pbar.update(1)

            # TODO: 1. seperate the annotation function (Decoupling) to outside of this function.
            # 2.check if seqhash same or not ----

        # LOGGER.warn("Sonar will delete a sample with empty alignment.")
        LOGGER.info("Error logs are kept under the given cache directory.")
        if list_fail_samples:
            LOGGER.info(f"Start paranoid alignment on {len(list_fail_samples)} sample.")
            # start process.
            # self.paranoid_align_multi(list_fail_samples, threads)
        count_sample = count_sample - len(list_fail_samples)
        LOGGER.info("Total inserted: " + str(count_sample))

    def _align(self, output_paranoid, qryfile, reffile, sample_name):
        # print(output_paranoid, qryfile, reffile, sample_name)

        if not os.path.exists(output_paranoid):
            aligner = sonarAligner(cache_outdir=self.basedir)

            ref, qry, cigar = aligner.align(
                aligner.read_seqcache(qryfile), aligner.read_seqcache(reffile)
            )
            with open(output_paranoid, "w+") as handle:
                handle.write(
                    ">original_"
                    + sample_name
                    + "\n"
                    + ref
                    + "\n>restored_"
                    + sample_name
                    + "\n"
                    + qry
                    + "\n"
                )
            logging.warn(
                f"See {output_paranoid} for alignment comparison. CIGAR:{cigar}"
            )

    def paranoid_align_multi(self, list_fail_samples, threads):  # noqa: C901
        l = len(list_fail_samples)
        with WorkerPool(n_jobs=threads, start_method="fork") as pool, tqdm(
            position=0,
            leave=True,
            desc="paranoid align...",
            total=l,
            unit="seqs",
            bar_format="{desc} {percentage:3.0f}% [{n_fmt}/{total_fmt}, {elapsed}<{remaining}, {rate_fmt}{postfix}]",
        ) as pbar:
            for _ in pool.imap_unordered(self._align, list_fail_samples):
                pbar.update(1)

    def paranoid_check(self, refseqs, sample_data, dbm):  # noqa: C901
        """
        This is the current version of paranoid test.
        It is linked to import_cached_samples

        Return:
            dict.
        """
        try:
            seq = list(refseqs[sample_data["sourceid"]])
        except Exception:
            refseqs[sample_data["sourceid"]] = list(
                dbm.get_sequence(sample_data["sourceid"])
            )
            seq = list(refseqs[sample_data["sourceid"]])
        prefix = ""
        gaps = {".", " "}
        sample_name = sample_data["name"]
        iter_dna_list = list(
            dbm.iter_dna_variants(sample_name, sample_data["sourceid"])
        )
        for vardata in iter_dna_list:
            if vardata["variant.alt"] in gaps:
                for i in range(vardata["variant.start"], vardata["variant.end"]):
                    seq[i] = ""
            elif vardata["variant.alt"] == ".":
                for i in range(vardata["variant.start"], vardata["variant.end"]):
                    seq[i] = ""
            elif vardata["variant.start"] >= 0:
                seq[vardata["variant.start"]] = vardata["variant.alt"]
            else:
                prefix = vardata["variant.alt"]

        ref_name = sample_data["refmol"]
        # seq is now a restored version from variant dict.
        seq = prefix + "".join(seq)
        with open(sample_data["seq_file"], "r") as handle:
            orig_seq = handle.read()

        if seq != orig_seq:
            self.log("[Paranoid-test] Fail sample:" + sample_name)
            logging.warn(
                f"Failure in sanity check: This {sample_name} sample will not be inserted to the database."
            )
            if not os.path.exists(self.error_dir):
                os.makedirs(self.error_dir)
            with open(
                os.path.join(self.error_dir, f"{sample_name}.error.var"), "w+"
            ) as handle:
                for vardata in iter_dna_list:
                    handle.write(str(vardata) + "\n")

            qryfile = os.path.join(
                self.error_dir, sample_name + ".error.restored_sam.fa"
            )
            reffile = os.path.join(
                self.error_dir, sample_name + ".error.original_sam.fa"
            )

            with open(qryfile, "w+") as handle:
                handle.write(seq)
            with open(reffile, "w+") as handle:
                handle.write(orig_seq)
            output_paranoid = os.path.join(
                self.basedir, f"{sample_name}.withref.{ref_name}.fail-paranoid.fna"
            )

            dbm.delete_alignment(
                seqhash=sample_data["seqhash"], element_id=sample_data["sourceid"]
            )
            # delete sample  if this sample didnt have any alignment and variant??.
            _return_ali_id = dbm.get_alignment_by_seqhash(
                seqhash=sample_data["seqhash"]
            )
            if len(_return_ali_id) == 0:
                dbm.delete_samples(sample_name)
                dbm.delete_seqhash(sample_data["seqhash"])

            return {
                "sample_name": sample_name,
                "qryfile": qryfile,
                "reffile": reffile,
                "output_paranoid": output_paranoid,
            }
        else:
            return {}

    def clear_uncessary_cache(self, samplefiles):
        for fname in samplefiles:
            with open(fname, "rb") as handle:
                data = pickle.load(handle, encoding="bytes")
                # clear uncessary file
                try:
                    os.remove(data["mafft_seqfile"])
                    os.remove(data["vcffile"])
                    os.remove(data["anno_vcf_file"])

                except OSError:
                    pass


if __name__ == "__main__":
    pass
