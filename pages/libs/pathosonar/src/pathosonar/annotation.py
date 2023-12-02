import json
import os
import subprocess

import pandas as pd

from .logging import LoggingConfigurator


# Initialize logger
LOGGER = LoggingConfigurator.get_logger()


class Annotator:
    def __init__(
        self, annotator_exe_path=None, SNPSIFT_exe_path=None, VCF_ONEPERLINE_PATH=None
    ) -> None:
        # "snpEff/SnpSift.jar"
        self.annotator = annotator_exe_path
        self.SNPSIFT = SNPSIFT_exe_path
        self.VCF_ONEPERLINE_TOOL = VCF_ONEPERLINE_PATH

    def snpeff_annotate(self, input_vcf, output_vcf, database_name):
        if not self.annotator or not os.path.isfile(self.annotator):
            raise ValueError("Annotator executable path is not provided.")
        # Command to annotate using SnpEff
        command = [f"java -jar {self.annotator} {database_name} {input_vcf} -noStats "]
        try:
            # Run the SnpEff annotation
            with open(output_vcf, "w") as output_file:
                result = subprocess.run(
                    command, shell=True, stdout=output_file, stderr=subprocess.PIPE
                )
            # result = subprocess.run(['java', '-version'], stderr=subprocess.STDOUT)
            if result.returncode != 0:
                LOGGER.error("Output failed with exit code: %s", result.returncode)
                print("Error output:", result.stderr.decode("utf-8"))

        except subprocess.CalledProcessError as e:
            LOGGER.error("Annotation failed: %s", e)

    def snpeff_transform_output(self, annotated_vcf, output_tsv):
        if not self.SNPSIFT:
            raise ValueError("SNPSIFT executable path is not provided.")

        # Command to transform SnpEff-annotated VCF to TSV
        transform_command = [
            f"cat {annotated_vcf} | perl {self.VCF_ONEPERLINE_TOOL} | java -jar {self.SNPSIFT} extractFields  -e '.' - 'CHROM' 'POS' 'REF' 'ANN[*].ALLELE' 'ANN[*].EFFECT' 'ANN[*].IMPACT' "
        ]

        try:
            # Run the transformation command
            with open(output_tsv, "w") as output_file:
                result = subprocess.run(
                    transform_command,
                    shell=True,
                    stdout=output_file,
                    stderr=subprocess.PIPE,
                )
            if result.returncode != 0:
                LOGGER.error("Output failed with exit code: %s", result.returncode)
                print("Error output:", result.stderr.decode("utf-8"))
        except subprocess.CalledProcessError as e:
            LOGGER.error("Output transformation failed: %s", e)


def read_tsv_snpSift(file_path: str) -> pd.DataFrame:
    """
    Process the TSV file from SnpSift, deduplicate the ANN[*].EFFECT column,
    remove values in ANN[*].IMPACT column, and split the records
    to have one effect per row.
    Returns the modified DataFrame.

    Parameters:
        file_path (str): Path to the input TSV file.

    Returns:
        pd.DataFrame: Modified DataFrame with deduplicated ANN[*].EFFECT column and one effect per row.

    Note:

    """
    try:
        # Read the TSV file into a DataFrame
        df = pd.read_csv(file_path, delimiter="\t")
        df = df.drop(["ANN[*].IMPACT"], axis=1, errors="ignore")
        df.rename(
            columns={"ANN[*].EFFECT": "EFFECT", "ANN[*].ALLELE": "ALT"},
            errors="raise",
            inplace=True,
        )
        # Deduplicate the values in the ANN[*].EFFECT column
        # df["EFFECT"] = df["EFFECT"].str.split(",").apply(set).str.join(",")
        # df['ANN[*].IMPACT'] = ''

        # Split the records into one effect per row
        # df = df.explode('ANN[*].EFFECT')
        df.drop_duplicates(inplace=True)

        # Reset the index
        df = df.reset_index(drop=True)
        # print(df)
        return df
    except KeyError as e:
        LOGGER.error(e)
        LOGGER.error(df.columns)
        raise
    except Exception as e:
        LOGGER.error(e)
        raise


def read_sonar_hash(file_path: str):

    with open(file_path, "r") as file:
        data = json.load(file)

    return data


def export_vcf_SonarCMD(
    db_path: str, refmol: str, sample_name: str, output_vcf: str
) -> None:
    sonar_cmd = [
        "sonar",
        "match",
        "--db",
        db_path,
        "-r",
        refmol,
        "--sample",
        sample_name,
        "--format",
        "vcf",
        "-o",
        output_vcf,
    ]
    try:
        subprocess.run(sonar_cmd, check=True)
        # print("Sonar command executed successfully.")
    except subprocess.CalledProcessError as e:
        print("Sonar match command failed:", e)


def import_annvcf_SonarCMD(db_path, sonar_hash, ann_input):

    sonar_cmd = [
        "sonar",
        "import-ann",
        "--db",
        db_path,
        "--sonar-hash",
        sonar_hash,
        "--ann-input",
        ann_input,
    ]
    try:
        subprocess.run(sonar_cmd, check=True)

        # print("Sonar command executed successfully.")
    except subprocess.CalledProcessError as e:
        print("Sonar import-ann command failed:", e)
