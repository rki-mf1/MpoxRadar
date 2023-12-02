#!/usr/bin/env bash
# VERSION="V.0.1"
# for example command:
# Usage: ./installation.bash --debug SNPEFF_DIR="/mnt/c/works/release/" NCBI_ACC="NC_063383.1"
#   --debug        Enable debug mode
#   SNPEFF_DIR     Directory where SnpEff will be installed
#   NCBI_ACC       NCBI accession number to build database from


##### Functions #####
# Print script usage
print_usage() {
    echo "Usage: $0 [--debug] SNPEFF_DIR=<directory_path> NCBI_ACC=<accession_number>"
    echo "  --debug        Enable debug mode"
      echo "  NCBI_ACC       NCBI accession number to build database from"
    echo "  SNPEFF_DIR     Directory where SnpEff will be installed"
}

set -e
START_TIME=$(date +%s)

for ARGUMENT in "$@"
do
        KEY=$(echo $ARGUMENT | cut -f1 -d=)
        VALUE=$(echo $ARGUMENT | cut -f2 -d=)
        case "$KEY" in
                SNPEFF_DIR)     SNPEFF_DIR=${VALUE} ;;
                NCBI_ACC)     NCBI_ACC=${VALUE} ;;
                --debug)        debug=1 ;;
                --help) print_usage; exit 0 ;;
                *)
        esac
done

# Check if no arguments are provided
if [ $# -eq 0 ]; then
    print_usage
    exit 1
fi

# Check if SNPEFF_DIR and NCBI_ACC are provided
if [ -z "$SNPEFF_DIR" ] || [ -z "$NCBI_ACC" ]; then
    echo "Error: SNPEFF_DIR and NCBI_ACC must be provided."
    print_usage
    exit 1
fi


# Check if JAVA is installed....


##### Initialize all Variables #####

##### SET UP Directory #####

mkdir -p $SNPEFF_DIR


##### Start #####
cd $SNPEFF_DIR

# Download latest version
# Check if the ZIP file already exists
if [ ! -f "snpEff_latest_core.zip" ]; then
    wget https://snpeff.blob.core.windows.net/versions/snpEff_latest_core.zip
fi

# Unzip file
unzip snpEff_latest_core.zip

echo "SnpEff has been installed in: $SNPEFF_DIR"

# Build database using NCBI accession number
echo "Building database for NCBI accession: $NCBI_ACC"

cp snpEff/snpEff.jar .
./snpEff/scripts/buildDbNcbi.sh $NCBI_ACC
