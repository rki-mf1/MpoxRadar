#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# author: Stephan Fuchs (Robert Koch Institute, MF1, fuchss@rki.de)
# , Kunaphas (RKI-HPI, kunaphas.kon@gmail.com)

# DEPENDENCIES
import collections
from contextlib import contextmanager
from datetime import datetime
import gzip
from hashlib import sha256
import json
import lzma
import os
import sys
from typing import Union
import zipfile

from Bio.Seq import Seq
import magic

from pathosonar.dbm import sonarDBManager
from pathosonar.logging import LoggingConfigurator
from pathosonar.utils_1 import get_filename_sonarhash
from . import __version__

# Initialize logger
LOGGER = LoggingConfigurator.get_logger()


# CLASS
class sonarBasics(object):
    """
    A class providing basic operations to application modules.
    """

    def __init__(self):
        pass
        # logging.basicConfig(format="%(asctime)s %(message)s")

    @staticmethod
    def get_version() -> str:
        """
        Retrieves the version of the covSonar package.
        """
        return __version__

    # FILE HANDLING
    @staticmethod
    @contextmanager
    def open_file_autodetect(file_path: str, mode: str = "r"):
        """
        Opens a file with automatic packing detection.

        Args:
            file_path: The path of the file to open.
            mode: The mode in which to open the file. Default is 'r' (read mode).

        Returns:
            A context manager yielding a file object.
        """
        # Use the magic library to identify the file type
        file_type = magic.from_file(file_path, mime=True)

        if file_type == "application/x-xz":
            file_obj = lzma.open(file_path, mode + "t")  # xz
        elif file_type == "application/gzip":
            file_obj = gzip.open(file_path, mode + "t")  # gz
        elif file_type == "application/zip":
            zip_file = zipfile.ZipFile(file_path, mode)  # zip
            # Assumes there's one file in the ZIP, adjust as necessary
            file_obj = zip_file.open(zip_file.namelist()[0], mode)
        elif file_type == "text/plain" or file_type == "application/csv":  # plain
            file_obj = open(file_path, mode)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        try:
            yield file_obj
        finally:
            file_obj.close()
            if file_type == "application/zip":
                zip_file.close()

    @staticmethod
    def _files_exist(*files: str) -> bool:
        """Check if files exits."""
        for fname in files:
            if not os.path.isfile(fname):
                return False
        return True

    @staticmethod
    def show_db_info(db):
        with sonarDBManager(db, readonly=True) as dbm:
            print("MPXSonar Version: ", sonarBasics.get_version())
            # print("database path:             ", dbm.dbfile)
            print("database version: ", dbm.get_db_version())
            print("database size: ", dbm.get_db_size())
            print("unique samples: ", dbm.count_samples())
            print("unique sequences: ", dbm.count_sequences())
            # print("Sample properties          ", dbm.get_earliest_import())
            # print("latest genome import:      ", dbm.get_latest_import())
            # print("earliest sampling date:    ", dbm.get_earliest_date())
            # print("latest sampling date:      ", dbm.get_latest_date())

    # vcf
    def exportVCF(cursor, reference, outfile=None, na="*** no match ***"):  # noqa: C901
        """
        This function is used to output vcf file and hash.sonar file

        Note:
            * One ref. per vcf
            * POS position in VCF format: 1-based position
            * Deletion? In the VCF file, the REF allele represents the reference sequence
            before the deletion, and the ALT allele represents the deleted sequence
            example:suppose we have
                Ref: atCga C is the reference base
                1:   atGga C base is changed to G
                2:   at-ga C base is deleted w.r.t. the ref.
            #CHROM  POS     ID      REF     ALT
            1       3       .       C       G
            1       2       .       TC      T

        """
        records = collections.OrderedDict()
        all_samples = set()
        sample_hash_list = {}
        IDs_list = {}

        for row in cursor.fetchall():  # sonarBasics.iter_formatted_match(cursor):
            # print(row)
            element_id, variant_id, chrom, pos, pre_ref, ref, alt, samples, seqhash = (
                row["element.id"],
                row["variant.id"],
                row["molecule.accession"],
                row["variant.start"],
                row["variant.pre_ref"],
                row["variant.ref"],
                row["variant.alt"],
                row["samples"],
                row["seqhash"],
            )
            # POS position in VCF format: 1-based position
            pos = pos + 1
            # print(chrom, pos, ref, alt, samples)
            # reference ID is used just for now
            if chrom not in records:
                records[chrom] = collections.OrderedDict()
            if pos not in records[chrom]:
                records[chrom][pos] = {}

            if ref not in records[chrom][pos]:
                records[chrom][pos][ref] = {}

            if pre_ref not in records[chrom][pos]:
                records[chrom][pos]["pre_ref"] = pre_ref

            if alt not in records[chrom][pos][ref]:
                records[chrom][pos][ref][alt] = []
            records[chrom][pos][ref][alt].append(samples)  # set(samples.split("\t"))

            # print(records)
            all_samples.update(samples.split("\t"))

            # handle the variant and sample.
            if samples not in IDs_list:
                IDs_list[samples] = []
            IDs_list[samples].append(
                {"element_id": element_id, "variant_id": variant_id}
            )

            # handle the hash and sample.
            sample_hash_list[samples] = seqhash

        # print(records)
        if len(records) != 0:
            all_samples = sorted(all_samples)

            if outfile is None:
                handle = sys.stdout
            else:
                # if not outfile.endswith(".gz"):
                # outfile += ".gz"

                os.makedirs(os.path.dirname(outfile), exist_ok=True)
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
                    # logging.info(
                    #    f"sample list output: '{filename_sonarhash}', this file is used when you want to reimport annotated data back to the database."
                    # )
                handle = open(outfile, mode="w")  # bgzf.open(outfile, mode='wb')

            # vcf header
            handle.write("##fileformat=VCFv4.2\n")
            handle.write(
                "##CreatedDate=" + datetime.now().strftime("%d/%m/%Y,%H:%M:%S") + "\n"
            )
            handle.write("##Source=pathoSonar" + sonarBasics().get_version() + "\n")
            # handle.write("##sonar_sample_hash="+str(sample_hash_list)+"\n")
            handle.write("##reference=" + reference + "\n")
            handle.write(
                '##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">\n'
            )
            handle.write(
                "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t"
                + "\t".join(all_samples)
                + "\n"
            )
            # records
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
                                # print(samples)

                                gts.append(
                                    ["1" if x in samples else "0" for x in all_samples]
                                )
                                alt_samples.update(samples)

                            # NOTE: this code part produce 0/1, 1/0
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
                                    pos - 1
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
            handle.close()
        else:
            print(na)

    @staticmethod
    def set_key(dictionary, key, value):
        if key not in dictionary:
            dictionary[key] = value
        elif type(dictionary[key]) == list:
            dictionary[key].append(value)
        else:
            dictionary[key] = [dictionary[key], value]
        return dictionary

    @staticmethod
    @contextmanager
    def out_autodetect(outfile=None):
        """
        Open a file if the 'outfile' is provided.
        If not, use standard output.

        Args:
            outfile: File path to the output file. If None, use standard output.
        """
        if outfile is not None:
            f = open(outfile, "w")
        else:
            f = sys.stdout
        try:
            yield f
        finally:
            if f is not sys.stdout:
                f.close()

    # SEQUENCE HANDLING
    def harmonize_seq(seq: str) -> str:
        """
        Harmonizes the input sequence.

        This function trims leading and trailing white spaces, converts the sequence to upper case and
        replaces all occurrences of "U" with "T". It's usually used to standardize the format of a DNA
        or RNA sequence.

        Args:
            seq (str): The input sequence as a string.

        Returns:
            str: The harmonized sequence.
        """
        try:
            return seq.strip().upper().replace("U", "T")
        except AttributeError as e:
            raise ValueError(
                f"Invalid input, expected a string, got {type(seq).__name__}"
            ) from e

    @staticmethod
    def hash_seq(seq: Union[str, Seq]) -> str:
        """
        Generate a hash from a sequence.

        Args:
            seq: The sequence to hash. This can either be a string or a Seq object from BioPython.

        Returns:
            The SHA-256 hash of the sequence.

        Notes:
            The SHA-256 hash algorithm is used as it provides a good balance
            between performance and collision resistance.
        """
        # If the input is a BioPython Seq object, convert it to a string.
        if isinstance(seq, Seq):
            seq = str(seq)

        return sha256(seq.upper().encode()).hexdigest()
