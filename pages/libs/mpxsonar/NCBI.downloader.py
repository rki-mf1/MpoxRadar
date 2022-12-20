#!/usr/bin/env python3
# Author: K2.
# Step in this File
# 1. Search query term and then get total count
# 2. load with batch size and save into tmp file.
# 3. Parse the record and save into tsv and fasta
# ----
# 4. log.log file to keep track process
# 5. .success to indicate this folder is ready to import.

import argparse
import datetime
import logging
import os
import sys
import time
import traceback
from urllib.error import HTTPError

from Bio import Entrez
from Bio import SeqIO
import dateparser
from dotenv import load_dotenv

load_dotenv()
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
REF_LIST = [
    "NC_063383.1",
    "ON563414.3",
    "MT903344.1",
]

Entrez.api_key = os.getenv("NCBI_API_KEY", "")
Entrez.tool = os.getenv("NCBI_TOOL", "")
Entrez.email = os.getenv("NCBI_EMAIL", "")  # Always tell NCBI who you are


def download(save_path):  # noqa: C901
    # nucleotide nuccore
    DB = "nucleotide"
    QUERY = "Monkeypox virus[Organism] AND complete[prop]"
    BATCH_SIZE = 10
    # 1
    # retmax=1 just returns first result of possibly many.
    attempt = 0
    success = False
    while attempt < 3 and not success:
        attempt += 1
        try:
            handle = Entrez.esearch(
                db=DB,
                term=QUERY,
                usehistory="y",
                idtype="acc",
            )

            record = Entrez.read(handle)
            total_count = record["Count"]
            logging.info("Total sample to download: %s " % (total_count))

            handle = Entrez.esearch(
                db=DB,
                term=QUERY,
                retmax=total_count,
                usehistory="y",
                idtype="acc",
            )
            record = Entrez.read(handle)
            # setup cache
            time.sleep(1)
            # print(record)
            id_list = record["IdList"]
            search_results = Entrez.read(Entrez.epost(DB, id=",".join(id_list)))
            webenv = search_results["WebEnv"]
            query_key = search_results["QueryKey"]
            time.sleep(1)
            success = True
        except Exception as e:
            logging.error("Error at %s", "getting ID", exc_info=e)
    handle.close()
    if attempt == 3 and not success:
        return False

    if not os.path.exists(os.path.join(save_path, ".download.log")):
        file_log_handler = open(os.path.join(save_path, ".download.log"), "w+")
    else:
        file_log_handler = open(os.path.join(save_path, ".download.log"), "r+")
    try:
        _start = int(file_log_handler.read())
        logging.info(f"Resume previous download: start at {_start}")
    except Exception:
        logging.warning(
            "Cannot resume previous download, we will start a new download."
        )
        _start = 0
    # 2
    for start in range(_start, int(total_count), BATCH_SIZE):
        end = min(int(total_count), start + BATCH_SIZE)
        logging.info("Going to download record %i to %i" % (start + 1, end))

        save_filename = os.path.join(save_path, f"MPX.{start}-{end}.GB")
        file_handler = open(save_filename, "w")
        attempt = 0
        success = False
        while attempt < 3 and not success:
            attempt += 1
            try:
                fetch_handle = Entrez.efetch(
                    db=DB,
                    rettype="gb",
                    retmode="text",
                    retstart=start,
                    retmax=BATCH_SIZE,
                    webenv=webenv,
                    query_key=query_key,
                    idtype="acc",
                )
                success = True
            except HTTPError as err:
                if 500 <= err.code <= 599:
                    logging.warning(f"Received error from server {err}")
                    logging.warning("Attempt {attempt} of 3")
                    time.sleep(5)
                if 400 == err.code:
                    logging.warning(f"Received error from server {err}")
                    logging.warning("Attempt {attempt} of 3")
                    time.sleep(5)
                else:
                    raise
            except Exception as e:
                logging.error("Error at %s", "download sample", exc_info=e)

        if attempt == 3 and not success:
            fetch_handle.close()
            file_handler.close()
            file_log_handler.close()
            return False

        data = fetch_handle.read()
        fetch_handle.close()

        file_handler.write(data)
        file_handler.close()
        # save  end .log
        file_log_handler.seek(0)
        file_log_handler.write(str(end))
        file_log_handler.truncate()
        time.sleep(2)

    with open(os.path.join(save_path, ".download.success"), "w") as f:
        f.writelines("done")

    file_log_handler.close()
    return True


def generate_outputfiles(save_download_path, save_final_path):  # noqa: C901

    list_of_GB = []
    for x in os.listdir(save_download_path):
        if x.endswith(".GB"):
            # Prints only text file present in My Folder
            list_of_GB.append(os.path.join(save_download_path, x))
    # TODO: remove reference genome from the list.

    # fasta & meta
    fasta_out_handler = open(os.path.join(save_final_path, "seq.fasta"), "w")
    meta_out_handler = open(os.path.join(save_final_path, "meta.tsv"), "w")
    header = [
        "ID",
        "ISOLATE",
        "LENGTH",
        "COUNTRY",
        "GEO_LOCATION",
        "RELEASE_DATE",
        "COLLECTION_DATE",
        "SEQ_TECH",
    ]
    meta_out_handler.write("\t".join(header) + "\n")  # Write the header line
    try:
        for _file in list_of_GB:
            logging.info("Load:" + _file)
            seq_GBrecords = list(SeqIO.parse(_file, "genbank"))
            for seq_record in seq_GBrecords:
                if seq_record.id in REF_LIST:
                    continue

                _isolate = ""
                _country = ""
                _geo_location = ""
                _NCBI_release_date = ""
                _collection_date = ""
                _seq_tech = ""
                # print("Dealing with GenBank record %s" % seq_record.id)

                fasta_out_handler.write(
                    ">%s |%s\n%s\n"
                    % (seq_record.id, seq_record.description, seq_record.seq)
                )

                # assume all keys are exit.
                if "isolate" in seq_record.features[0].qualifiers:
                    _isolate = seq_record.features[0].qualifiers["isolate"][0]
                if "country" in seq_record.features[0].qualifiers:
                    _geo_location = seq_record.features[0].qualifiers["country"][0]
                    # extract country only
                    _country = _geo_location.split(":")[0]

                if "collection_date" in seq_record.features[0].qualifiers:
                    _collection_date = seq_record.features[0].qualifiers[
                        "collection_date"
                    ][0]
                    # 1.) need to fix date Nov-2017 -> 2017-11-01, 09-Nov-2017 -> 2017-11-09
                    # 1995 -> 1995-01-01 set default value with first day of
                    # the month and first month of the year
                    # 2.) Year needs to be present in the format.

                    d = dateparser.parse(
                        _collection_date,
                        settings={
                            "PREFER_DAY_OF_MONTH": "first",
                            "DATE_ORDER": "YMD",
                            "REQUIRE_PARTS": ["year"],
                            "RELATIVE_BASE": datetime.datetime(2022, 1, 1),
                        },
                    )
                    _collection_date = d.strftime("%Y-%m-%d")

                if (
                    "structured_comment" in seq_record.annotations
                    and "Assembly-Data" in seq_record.annotations["structured_comment"]
                    and "Sequencing Technology"
                    in seq_record.annotations["structured_comment"]["Assembly-Data"]
                ):
                    _seq_tech = seq_record.annotations["structured_comment"][
                        "Assembly-Data"
                    ]["Sequencing Technology"]

                if "date" in seq_record.annotations:
                    _NCBI_release_date = seq_record.annotations["date"]
                    # need to fix date 18-NOV-2022 -> 2022-11-18
                    d = dateparser.parse(
                        _NCBI_release_date,
                        settings={"PREFER_DAY_OF_MONTH": "first", "DATE_ORDER": "YMD"},
                    )
                    _NCBI_release_date = d.strftime("%Y-%m-%d")

                meta_out_handler.write(
                    "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n"
                    % (
                        seq_record.id,
                        _isolate,
                        len(seq_record),
                        _country,
                        _geo_location,
                        _NCBI_release_date,
                        _collection_date,
                        _seq_tech,
                    )
                )
    except Exception:
        fasta_out_handler.close()
        meta_out_handler.close()
        logging.exception(f"Error in {seq_record.id} !!")
        traceback.print_exc()
        return False

    fasta_out_handler.close()
    meta_out_handler.close()
    return True


def run(args):
    # logging.info("api_key:" + Entrez.api_key)
    # logging.info("tool:" + Entrez.tool)
    # logging.info("email:" + Entrez.email)
    if args.date:
        TODAY_DATE = args.date
    else:
        TODAY_DATE = datetime.datetime.now().strftime("%Y-%m-%d")

    if args.output:
        SAVE_PATH = args.output
    else:
        SAVE_PATH = os.path.join(os.getenv("SAVE_PATH", ""), TODAY_DATE)
    if not os.path.exists(SAVE_PATH):
        os.makedirs(SAVE_PATH)

    logging.basicConfig(
        format="NCBI-DL:%(asctime)s %(levelname)-4s: %(message)s",
        level=LOG_LEVEL,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(os.path.join(SAVE_PATH, "debug.log")),
            logging.StreamHandler(),
        ],
    )
    logging.info("Script version: 1")
    logging.info("Save output to:" + SAVE_PATH)

    save_download_path = os.path.join(SAVE_PATH, "GB")
    if not os.path.exists(save_download_path):
        os.makedirs(save_download_path)

    save_final_path = os.path.join(SAVE_PATH, "output")
    if not os.path.exists(save_final_path):
        os.makedirs(save_final_path)
    #
    logging.info("--- Download samples ---")
    if not os.path.exists(os.path.join(SAVE_PATH, "GB", ".download.success")):
        if download(save_download_path):
            logging.info("Download completed")
        else:
            logging.error("Download stop before it is finished")
            sys.exit("Please rerun it again later.")
    else:
        logging.info("Download completed, continue to process on GeneBank files.")

    # 3
    logging.info("--- Convert GeneBank to fasta and meta file ---")
    if not os.path.exists(os.path.join(SAVE_PATH, ".success")):
        if generate_outputfiles(save_download_path, save_final_path):

            logging.info("Processing completed")
        else:
            logging.error("Process stop before it is finished")
            sys.exit("Please rerun it again later.")

        with open(os.path.join(SAVE_PATH, ".success"), "w+") as f:
            f.write("done")
    logging.info("--- Done ---")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-d",
        "--date",
        type=lambda s: datetime.datetime.strptime(s, "%Y-%m-%d"),
        help="Date use for download.",
    )
    parser.add_argument("-o", "--output", type=str, help="Output")
    args = parser.parse_args()
    run(args)
