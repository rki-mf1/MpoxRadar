#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# author: Stephan Fuchs (Robert Koch Institute, MF1, fuchss@rki.de)
# , Kunaphas (RKI-HPI, kunaphas.kon@gmail.com)
import logging
import os
import pickle
import re
import sys

from Bio.Align.Applications import MafftCommandline
from Bio.Emboss.Applications import StretcherCommandline
import pandas as pd
import parasail
import psutil

from .config import TMP_CACHE


class sonarAligner(object):
    """
    this object performs a pairwise sequence alignment and provides/stores selected
    alignment functionalities/statistics.
    """

    def __init__(self, cache_outdir=None, method=1):
        self.nuc_profile = []
        self.nuc_n_profile = []
        self.aa_profile = []
        self.aa_n_profile = []
        self.cigar_pattern = re.compile(r"(\d+)(\D)")
        self.outdir = TMP_CACHE if not cache_outdir else os.path.abspath(cache_outdir)
        self.logfile = open(os.path.join(self.outdir, "align.debug.log"), "a")
        self.method = method

    def read_seqcache(self, fname):
        with open(fname, "r") as handle:
            seq = handle.readline().strip()
        return seq

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self.logfile:
            self.logfile.close()

    def log(self, msg, die=False, errtype="error"):
        if self.logfile:
            self.logfile.write(msg + "\n")
        elif not die:
            sys.stderr.write(msg + "\n")
        else:
            exit(errtype + ": " + msg)

    def cal_seq_length(self, seq, msg=""):
        lower_bound = (len(seq) * 97) / 100
        upper_bound = (len(seq) * 103) / 100
        self.log(seq)
        self.log(msg + "=" + " LO:" + str(lower_bound) + "UP:" + str(upper_bound))
        self.log("#----------#")

    # gapopen=16, gapextend=4
    # gapopen=10, gapextend=1
    def align(self, qryseq, refseq, gapopen=16, gapextend=4):
        """Method for parasail run"""
        result = parasail.sg_trace(
            qryseq, refseq, gapopen, gapextend, parasail.blosum62
        )
        return (
            result.traceback.ref,
            result.traceback.query,
            result.get_cigar().decode.decode(),
        )

    def align_MAFFT(self, input_fasta):
        mafft_exe = "mafft"
        mafft_cline = MafftCommandline(
            mafft_exe, input=input_fasta, inputorder=True, auto=True
        )
        stdout, stderr = mafft_cline()
        # find the fist position of '\n' to get seq1
        s1 = stdout.find("\n") + 1
        # find the start of second sequence position
        e = stdout[1:].find(">") + 1
        # find the '\n' of the second sequence to get seq2
        s2 = stdout[e:].find("\n") + e
        ref = stdout[s1:e].replace("\n", "").upper()
        qry = stdout[s2:].replace("\n", "").upper()
        return qry, ref

    def align_Stretcher(self, qry, ref, gapopen=16, gapextend=4):
        """Method for handling emboss stretcher run

        Return:
        """
        try:
            cline = StretcherCommandline(
                asequence=qry,
                bsequence=ref,
                gapopen=gapopen,
                gapextend=gapextend,
                outfile="stdout",
                aformat="fasta",
                # datafile="EDNAFULL", auto set by strecher
            )
            stdout, stderr = cline()
            # self.cal_seq_length(stdout[0:20], msg="stdout")
            # find the fist position of '\n' to get seq1
            s1 = stdout.find("\n") + 1
            # find the start of second sequence position
            e = stdout[1:].find(">") + 1
            # find the '\n' of the second sequence to get seq2
            s2 = stdout[e:].find("\n") + e
            qry = stdout[s1:e].replace("\n", "")
            ref = stdout[s2:].replace("\n", "")
            # self.cal_seq_length(qry, msg="qry")
            # self.cal_seq_length(ref, msg="ref")
        except Exception:
            try:
                for proc in psutil.process_iter():
                    # Get process name & pid from process object.
                    processName = proc.name()
                    processID = proc.pid
                    if (
                        "stretcher" in processName or "stretcher" in proc.cmdline()
                    ):  # adapt this line to your needs
                        logging.info(
                            f"Kill {processName}[{processID}] : {''.join(proc.cmdline())})"
                        )
                        proc.terminate()
                        proc.kill()
            except psutil.NoSuchProcess:
                pass
            logging.error(
                "Stop process during alignment; to rerun again, you may need to provide a new cache directory."
            )
            sys.exit("exited after ctrl-c")

        return qry, ref

    def process_cached_sample(self, fname):
        if self.method == 1:  # MAFFT
            process_flag = self.process_cached_v1(fname)
        elif self.method == 2:  # Parasail
            process_flag = self.process_cached_v2(fname)
        return process_flag

    def process_cached_v1(self, fname):
        """
        Work with: Emboss Stretcher, Mafft
        This function takes a sample file and processes it.
        create var file with NT and AA mutations
        """
        with open(fname, "rb") as handle:
            data = pickle.load(handle, encoding="bytes")

        if data["var_file"] is None:
            return True
        elif os.path.isfile(data["var_file"]):
            with open(data["var_file"], "r") as handle:
                for line in handle:
                    pass
            if line == "//":
                return True

        sourceid = str(data["source_acc"])
        self.log("data:" + str(data))
        # alignment = self.align(data["seq_file"], data["ref_file"])
        alignment = self.align_MAFFT(data["mafft_seqfile"])
        # print(alignment[0][0:20]) qry
        # print(alignment[1][0:20]) ref
        nuc_vars = [x for x in self.extract_vars(*alignment, elem_acc=sourceid)]
        vars = "\n".join(["\t".join(x) for x in nuc_vars])
        if nuc_vars:
            # create AA mutation
            aa_vars = "\n".join(
                [
                    "\t".join(x)
                    for x in self.lift_vars(
                        nuc_vars, data["lift_file"], data["tt_file"]
                    )
                ]
            )
            if aa_vars:
                # concatinate to the same file of NT variants
                vars += "\n" + aa_vars
            vars += "\n"
        try:
            with open(data["var_file"], "w") as handle:
                handle.write(vars + "//")
        except OSError:
            os.makedirs(os.path.dirname(data["var_file"]), exist_ok=True)
            with open(data["var_file"], "w") as handle:
                handle.write(vars + "//")
        return True

    def process_cached_v2(self, fname):
        """
        Work with: Cigar format
        This function takes a sample file and processes it.
        create var file with NT and AA mutations
        """

        with open(fname, "rb") as handle:
            data = pickle.load(handle, encoding="bytes")

        if data["var_file"] is None:
            return True
        elif os.path.isfile(data["var_file"]):
            with open(data["var_file"], "r") as handle:
                for line in handle:
                    pass
            if line == "//":
                return True

        self.log("data:" + str(data))
        # sourceid = str(data["sourceid"])
        # alignment = self.align(data["seq_file"], data["ref_file"])
        # self.cal_seq_length(alignment[0][0:20], msg="qry")
        # self.cal_seq_length(alignment[1][0:20], msg="ref")
        # nuc_vars = [x for x in self.extract_vars(*alignment, sourceid)]

        # elemid = str(data["sourceid"])
        source_acc = str(data["source_acc"])
        qryseq = self.read_seqcache(data["seq_file"])
        refseq = self.read_seqcache(data["ref_file"])
        _, __, cigar = self.align(qryseq, refseq)
        nuc_vars = [
            x
            for x in self.extract_vars_from_cigar(
                qryseq, refseq, cigar, source_acc, data["cds_file"]
            )
        ]

        vars = "\n".join(["\t".join(x) for x in nuc_vars])
        if nuc_vars:
            # create AA mutation
            aa_vars = "\n".join(
                [
                    "\t".join(x)
                    for x in self.lift_vars(
                        nuc_vars, data["lift_file"], data["tt_file"]
                    )
                ]
            )
            if aa_vars:
                # concatenate to the same file of NT variants
                vars += "\n" + aa_vars
            vars += "\n"
        try:
            with open(data["var_file"], "w") as handle:
                handle.write(vars + "//")
        except OSError:
            os.makedirs(os.path.dirname(data["var_file"]), exist_ok=True)
            with open(data["var_file"], "w") as handle:
                handle.write(vars + "//")
        return True

    def extract_vars(self, qry_seq, ref_seq, elem_acc):
        """
        Note:
            Use element accession
            Add element type
            Frameshift is no longer used here
        """
        query_length = len(qry_seq)
        if query_length != len(ref_seq):
            sys.exit("error: sequences differ in length")
        qry_seq += " "
        ref_seq += " "
        i = 0
        offset = 0
        while i < query_length:
            # match
            if qry_seq[i] == ref_seq[i]:
                pass
            # deletion
            elif qry_seq[i] == "-":
                s = i
                while qry_seq[i + 1] == "-":
                    i += 1
                start = s - offset
                end = i + 1 - offset
                if end - start == 1:
                    label = "del:" + str(start + 1)
                else:
                    label = "del:" + str(start + 1) + "-" + str(end)
                yield ref_seq[s : i + 1], str(start), str(
                    end
                ), " ", elem_acc, label, "nt"

            # insertion
            elif ref_seq[i] == "-":
                s = i - 1
                while ref_seq[i + 1] == "-":
                    i += 1
                # insertion at pos 0
                if s == -1:
                    ref = "."
                    alt = qry_seq[: i + 1]
                else:
                    ref = ref_seq[s]
                    alt = qry_seq[s : i + 1]
                pos = s - offset + 1
                yield ref, str(pos - 1), str(pos), alt, elem_acc, ref + str(
                    pos
                ) + alt, "nt"
                offset += i - s
            # snps
            else:
                ref = ref_seq[i]
                alt = qry_seq[i]
                pos = i - offset + 1
                yield ref, str(pos - 1), str(pos), alt, elem_acc, ref + str(
                    pos
                ) + alt, "nt"
            i += 1

    """
    def extract_vars(self, qry_seq, ref_seq, elemid):
    """
    """
        extract variant code for the Emboss Stretcher and MAFFT output.

        NOTE: Frameshift is fixed with 0
    """
    """
        query_length = len(qry_seq)
        if query_length != len(ref_seq):
            sys.exit("error: sequences differ in length")
        qry_seq += " "
        ref_seq += " "
        i = 0
        offset = 0
        while i < query_length:
            # match
            if qry_seq[i] == ref_seq[i]:
                pass
            # deletion
            elif qry_seq[i] == "-":
                s = i
                while qry_seq[i + 1] == "-":
                    i += 1
                start = s - offset
                end = i + 1 - offset
                if end - start == 1:
                    label = "del:" + str(start + 1)
                else:
                    label = "del:" + str(start + 1) + "-" + str(end)
                yield ref_seq[s : i + 1], str(start), str(end), " ", elemid, label, "0"

            # insertion
            elif ref_seq[i] == "-":
                s = i - 1
                while ref_seq[i + 1] == "-":
                    i += 1
                # insertion at pos 0
                if s == -1:
                    ref = "."
                    alt = qry_seq[: i + 1]
                else:
                    ref = ref_seq[s]
                    alt = qry_seq[s : i + 1]
                pos = s - offset + 1
                yield ref, str(pos - 1), str(pos), alt, elemid, ref + str(
                    pos
                ) + alt, "0"
                offset += i - s
            # snps
            else:
                ref = ref_seq[i]
                alt = qry_seq[i]
                pos = i - offset + 1
                yield ref, str(pos - 1), str(pos), alt, elemid, ref + str(
                    pos
                ) + alt, "0"
            i += 1
    """

    def translate(self, seq, tt):
        aa = []
        while len(seq) % 3 != 0:
            seq = seq[: len(seq) - 1]
        for codon in [seq[i : i + 3] for i in range(0, len(seq), 3)]:
            aa.append(tt[codon])
        return "".join(aa)

    def lift_vars(self, nuc_vars, lift_file, tt_file):  # noqa: C901
        df = pd.read_pickle(lift_file)
        # print(df)
        with open(tt_file, "rb") as handle:
            tt = pickle.load(handle, encoding="bytes")
        for nuc_var in nuc_vars:
            if nuc_var[3] == ".":
                continue  # ignore uncovered terminal regions
            for i in range(int(nuc_var[1]), int(nuc_var[2])):
                alt = "-" if nuc_var[3] == " " else nuc_var[3]
                df.loc[df["nucPos1"] == i, "alt1"] = alt
                df.loc[df["nucPos2"] == i, "alt2"] = alt
                df.loc[df["nucPos3"] == i, "alt3"] = alt
        # what if it is empty
        df = df.loc[
            (df["ref1"] != df["alt1"])
            | (df["ref2"] != df["alt2"])
            | (df["ref3"] != df["alt3"])
        ]
        prev_row = None
        if not df.empty:
            df["altAa"] = df.apply(
                lambda x: self.translate(x["alt1"] + x["alt2"] + x["alt3"], tt), axis=1
            )
            df = df.loc[df["aa"] != df["altAa"]]

            # snps or inserts
            for index, row in df.loc[
                (df["altAa"] != "-") & (df["altAa"] != "")
            ].iterrows():
                pos = row["aaPos"] + 1
                label = row["aa"] + str(pos) + row["altAa"]
                yield row["aa"], str(pos - 1), str(pos), row["altAa"], str(
                    row["accession"]
                ), label, "cds"

            # deletions
            for index, row in (
                df.loc[(df["altAa"] == "-")].sort_values(["elemid", "aaPos"]).iterrows()
            ):
                if prev_row is None:
                    prev_row = row
                elif (
                    prev_row["elemid"] == row["elemid"]
                    and abs(prev_row["aaPos"] - row["aaPos"]) == 1
                ):
                    prev_row["aa"] += row["aa"]
                else:
                    start = prev_row["aaPos"]
                    end = prev_row["aaPos"] + len(prev_row["aa"])
                    if end - start == 1:
                        label = "del:" + str(start + 1)
                    else:
                        label = "del:" + str(start + 1) + "-" + str(end)
                    yield prev_row["aa"], str(start), str(end), " ", str(
                        prev_row["accession"]
                    ), label, "cds"
                    prev_row = row

        if prev_row is not None:
            start = prev_row["aaPos"]
            end = prev_row["aaPos"] + len(prev_row["aa"])
            if end - start == 1:
                label = "del:" + str(start + 1)
            else:
                label = "del:" + str(start + 1) + "-" + str(end)
            yield prev_row["aa"], str(start), str(end), " ", str(
                prev_row["accession"]
            ), label, "cds"

    def extract_vars_from_cigar(
        self, qryseq, refseq, cigar, elemid, cds_file
    ):  # noqa: C901
        # get annotation for frameshift detection
        # cds_df = pd.read_pickle(cds_file)
        # cds_set = set(cds_df[cds_df["end"] == 0])

        # extract
        refpos = 0
        qrypos = 0
        qrylen = len(qryseq)
        prefix = False
        vars = []
        for match in self.cigar_pattern.finditer(cigar):
            vartype = match.group(2)
            varlen = int(match.group(1))
            # identical sites
            if vartype == "=":
                refpos += varlen
                qrypos += varlen
            # snp handling
            elif vartype == "X":
                for x in range(varlen):
                    ref = refseq[refpos]
                    alt = qryseq[qrypos]
                    vars.append(
                        (
                            ref,
                            str(refpos),
                            str(refpos + 1),
                            alt,
                            elemid,
                            ref + str(refpos + 1) + alt,
                            "nt",
                        )
                    )
                    refpos += 1
                    qrypos += 1
            # deletion handling
            elif vartype == "D":
                if (
                    refpos == 0 and prefix is False
                ) or qrypos == qrylen:  # deletion at sequence terminus
                    vars.append(
                        (
                            refseq[refpos : refpos + varlen],
                            str(refpos),
                            str(refpos + varlen),
                            ".",
                            elemid,
                            "del:" + str(refpos + 1) + "-" + str(refpos + varlen),
                            "nt",
                        )
                    )
                    refpos += varlen
                elif varlen == 1:  # 1bp deletion
                    vars.append(
                        (
                            refseq[refpos],
                            str(refpos),
                            str(refpos + 1),
                            " ",
                            elemid,
                            "del:" + str(refpos + 1),
                            "nt"
                            # self.detect_frameshifts(
                            #    refpos, refpos + 1, " ", cds_df, cds_set
                            # ),
                        )
                    )
                    refpos += 1
                else:  # multi-bp inner deletion
                    vars.append(
                        (
                            refseq[refpos : refpos + varlen],
                            str(refpos),
                            str(refpos + varlen),
                            " ",
                            elemid,
                            "del:" + str(refpos + 1) + "-" + str(refpos + varlen),
                            "nt"
                            # self.detect_frameshifts(
                            #    refpos, refpos + varlen, " ", cds_df, cds_set
                            # ),
                        )
                    )
                    refpos += varlen
            # insertion handling
            elif vartype == "I":
                if refpos == 0:  # to consider insertion before sequence start
                    ref = "."
                    alt = qryseq[:varlen]
                    prefix = True
                    # fs = "0"
                else:
                    ref = refseq[refpos - 1]
                    alt = qryseq[qrypos - 1 : qrypos + varlen]
                    # fs = self.detect_frameshifts(
                    #     refpos - 1, refpos, alt, cds_df, cds_set
                    # )
                vars.append(
                    (
                        ref,
                        str(refpos - 1),
                        str(refpos),
                        alt,
                        elemid,
                        ref + str(refpos) + alt,
                        "nt"
                        # fs,
                    )
                )
                qrypos += varlen
            # unknown
            else:
                sys.exit(
                    "error: Sonar cannot interpret '" + vartype + "' in cigar string."
                )
        return vars

    def detect_frameshifts(self, start, end, alt, cds_df, coding_sites_set):
        # handling deletions
        if alt == " " or alt == "":
            coords = set(range(start, end))
            cds_df["gap"] = cds_df.apply(lambda x: 1 if x.pos in coords else 0, axis=1)
            groups = cds_df.groupby(
                [cds_df["elemid"], (cds_df["gap"].shift() != cds_df["gap"]).cumsum()]
            ).agg({"gap": sum})
            for _, row in groups.iterrows():
                if row["gap"] % 3 != 0:
                    print(f"D Found frameshifts: {start} {end}")
                    return "1"
        # handling insertions
        elif (len(alt) - 1) % 3 > 0 and start in coding_sites_set:
            print(f"I Found frameshifts: {start} {end}")
            return "1"
        return "0"

    # deprecated var extractor from aligned sequence strings
    def extract_vars_dep(self, qry_seq, ref_seq, elemid):  # noqa: C901
        query_length = len(qry_seq)
        if query_length != len(ref_seq):
            sys.exit("error: sequences differ in length")
        qry_seq += " "
        ref_seq += " "
        i = 0
        offset = 0
        while i < query_length:
            # match
            if qry_seq[i] == ref_seq[i]:
                pass
            # deletion
            elif qry_seq[i] == "-":
                s = i
                while qry_seq[i + 1] == "-":
                    i += 1
                start = s - offset
                end = i + 1 - offset
                if (
                    start == 0 or end == query_length
                ):  # handle deletions at sequence termini
                    for k in range(start, end):
                        ref = ref_seq[k]
                        pos = k - offset + 1
                        yield ref, str(pos - 1), str(pos), ".", elemid, " "
                else:  # 'real' (inner) deletions
                    if end - start == 1:
                        label = "del:" + str(start + 1)
                    else:
                        label = "del:" + str(start + 1) + "-" + str(end)
                    yield ref_seq[s : i + 1], str(start), str(end), " ", elemid, label

            # insertion
            elif ref_seq[i] == "-":
                s = i - 1
                while ref_seq[i + 1] == "-":
                    i += 1
                # insertion at pos 0
                if s == -1:
                    ref = "."
                    alt = qry_seq[: i + 1]
                else:
                    ref = ref_seq[s]
                    alt = qry_seq[s : i + 1]
                pos = s - offset + 1
                yield ref, str(pos - 1), str(pos), alt, elemid, ref + str(pos) + alt
                offset += i - s
            # snps
            else:
                ref = ref_seq[i]
                alt = qry_seq[i]
                pos = i - offset + 1
                yield ref, str(pos - 1), str(pos), alt, elemid, ref + str(pos) + alt
            i += 1
