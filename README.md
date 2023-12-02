# pathoSonar

pathoSonar is an extension of Covsonar (the database-driven system for handling genomic sequences of SARS-CoV-2 and screening genomic profiles, developed at the RKI (https://github.com/rki-mf1/covsonar).) that adds support for multiple genome references and quick processing with MariaDB.


## Prerequisite software

1. Basic dependencies
```sh
# for sonar tool.
sudo apt-get install python3-dev default-libmysqlclient-dev build-essential
# for annotation tool.
sudo apt-get install curl sudo apt install default-jre
```
2. Install MariaDB server (MySQL should work too!, not tested yet).
3. Install Conda environment.

## 1. pathoSonar Installation.
Currently, the pathoSonar is not available at the pip&conda repository.

### Stable version.🔖
1. clone from (master branch)
```sh
# 1. Git clone
git clone https://github.com/rki-mf1/pathoSonar
# 2. Install env.
conda create -n pathoSonar python=3.11 poetry

conda activate pathoSonar  # needs to be activated for the following commands to work

cd pathoSonar
```
3.There is a ".env.template" file in the root directory. This file contains variables
that must be used in the program and may differ depending on the environment.
The ".env.template" file should be copied and changed to ".env",
and then the variables should be edited accordingly.

2.
```sh
# 4. Install pathSonar env.
poetry install --no-dev
# 5. Test
sonar -v
```

3. Install Snpeff
```
bash installation.bash --debug SNPEFF_DIR="/mnt/c/works/release/" NCBI_ACC="NC_063383.1"
```

4. edit .env file

### Dev. version.🚧
every installation step is same as stable version, but the code is in "dev branch".
```sh
git fetch
git checkout dev
```


## Quickstart

```sh
# Setup database
sonar setup
# Add properties
sonar add-prop --name COLLECTION_DATE --dtype date --descr "sampling date"
sonar add-prop --name GENOME_COMPLETENESS --dtype text --descr "genome completeness"
sonar add-prop --name LENGTH --dtype integer --descr "sequence length"
# Import  samples
sonar import --fasta example-data/mpox.fasta --tsv example-data/mpox.tsv --threads 5 --cache ../tmp_cache  --cols sample=ID --auto-link
# Query
sonar match
```

## 2. Usage

In pathoSonar, the table below shows the several commands that can be called.

| subcommand | purpose                                                             |
|------------|---------------------------------------------------------------------|
| setup      | set up a new database.                                  |
| import     | import genome sequences and sample information to the database     |
| list-prop  | view sample properties added to the database             |
| add-prop    | add a sample property to the database                    |
| delete-prop       | delete a sample property from the database |
| match   |  Get mutations profiles based on a given query                                        |
| restore   | Restore sequence(s) from the database                                         |
| info   |  Show software and database info.                                        |
| optimize   | Optimizes the database                                         |
| add-ref   | Add a reference genome to the database              |
| delete-ref   | Delete a reference genome in database       |
| list-ref   | View all references in the database                        |
| import-ann   | Import annotated variant from the SnpEff tool     |

Each tool provides a help page that can be accessed with the `-h` option.

```sh
# display help page
sonar -h
# display help page for each tool
sonar import -h
```

### 2.1 Setup a database (setup ⛽)

First, we have to create a new database instance. (if we already configure detail in the .env file.)
```sh
sonar setup
```
Or we can create a new database with a defined URL.
```sh
sonar setup --db https://super_user:123456@localhost:3306/mpx
```

> Attention ⚠️: The database name is a fixed name, namely "mpx".

> Attention ⚠️: If you already set up .env file, then there is no need to add the --db tag in the command. The rest of our example command will not include the "--db" tag. We assume there is the .env file on your system.

> Note 🕯️: By default, NC_063383.1 (Monkeypox virus) is used as a reference when running the setup command. If we want to set up a database for a different reference genome, we can provide `--gbk` following the Genbank file. [how to download genbank file](https://ncbiinsights.ncbi.nlm.nih.gov/2017/05/08/genome-data-download-made-easy/).
```sh
sonar setup --db test.db --auto-create --gbk MT903344.1.gb
```

### 2.2 Property management (`list-prop`, `add-prop` and `delete-prop`)

In pathoSonar, users can now arbitrarily add meta information or properties into a database to fit a specific project objective.

To add properties, we can use the `add-prop` command to add meta information into the database.

The required arguments are listed below when we use `add-prop` command
* `--name`, name of sample property
* `--descr`, description of the new property
* `--dtype`, data type of the new property (e.g., 'integer', 'float', 'text', 'date', 'zip')

```sh
# for example
sonar add-prop --name LINEAGE --dtype text --descr "Store Lineage"
#
sonar add-prop --name AGE --dtype integer --descr "patient age (example)"
#
sonar add-prop --name COLLECTION_DATE --dtype date --descr "sampling date"
```
> TIP 🕯️: `sonar add-prop -h ` to see all available arguments.

⚠️ WARNING: We reserve **'sample'** keyword, so you cannot use this name as a property.
(e.g., ⛔❌`--name sample`) because we use this name as the ID in the database schema.⚠️

To view the added properties, we can use the `list-prop` command to display all information.
```sh
sonar list-prop
```

The `delete-prop` command is used to delete an unwanted property from the database.

```sh
sonar delete-prop --name SEQ_REASON
```

The program will ask for confirmation of the action.
```
Do you really want to delete this property? [YES/no]: YES
```

### 2.3 Reference Management (add-ref, list-ref, delete-ref).

> NOTE 📌: [how to download genbank file](https://ncbiinsights.ncbi.nlm.nih.gov/2017/05/08/genome-data-download-made-easy/)

Add new reference.
```sh
sonar add-ref --gbk MT903344.1.gb
```
>⚠️ Attention: Some references did not annotate a gene name but just gave only "locus_tag" in the GenBank file. The program will use "locus_tag" instead of the gene name when adding to the database. This annotation will affect the search (match) command for protein mutation.
For example, we want to search for the D88K mutation. The reference MT903344.1 used "MPXV-UK_" as the protein ID, so when we perform the search, we will write it as "MPXV-UK_P2-076:D88K", while the NC_063383.1 use "OPG093" (e.g., OPG093:D88K).

List all references in a database
```sh
sonar list-ref
```

Delete reference.
```sh
sonar delete-ref -r MT903344.1
```

### 2.4 Adding genomes and meta information to the database (`import` command)

This example shows how we add sequence along with meta information to a database.

let's assume we have sequence file name `valid.fasta` and meta-info file name `day.tsv`.

valid.fasta
```
>IMS-00113
CCAACCAACTTTCGATCTCTTG
```

day.tsv
```
IMS_ID          COLLECTION_DATE	    SEQ_TECH
IMS-00113	2021-02-04		    Illumina NovaSeq 6000
```

The required argument for the `import` command are listed as follows;

1. `--fasta` a fasta file containing genome sequences to be imported. A compressed file of fasta is also valid as an input (e.g., `--fasta sample.fasta.gz` or `sample.fasta.xz`).

2. `--tsv` a tab-delimited file containing sample properties to be imported.

3. `--cache` a directory for caching data.

4. `--cols` define column names for sample properties.

So, example
```sh
sonar import --fasta valid.fasta --tsv day.tsv --threads 10 --cache tmp_cache  --cols sample=IMS_ID
```
As you can see, we defined `--cols sample=IMS_ID`, in which `IMS_ID` is the ID that linked the sample name between the fasta file and meta-info file, and `sample` is the reserved word used to link data between tables in the database.

> TIP 🕯️: You might don't need to create an `ID` property because we use the `sample` keyword as the unique key to link data in our database schema and also used in the query command, which you will see in the next section.

> TIP 🕯️: use `--threads` to increase the performance.

> TIP 🕯️: use `--cache` to choose a folder for the cache files, so next time we don't need to do preprocessing step.

To update meta information when we add a new property, we can use the same `import` command, but this time, in the `--tsv` tag, we provide a new meta or updated file, for example:
```sh
sonar import --tsv meta.passed.tsv --threads 64 --cache tmp_cache --cols sample=IMS_ID

```
> NOTE 🤨: please make sure the `--cols sample=IMS_ID` is correctly referenced. If you have a different column name, please change it according to the meta-info file (for example, `--cols sample=IMS_NEW_ID`)

### 2.5 Query genome sequences based on profiles (match command)

Genomic profiles can be defined to align genomes. For this purpose, the variants related to the complete genome of the Monkeypox virus, NCBI Reference Sequence (NC_063383.1) must be expressed as follows:

| type       | nucleotide level                                                  | amino acid level              |
|-----------|-------------------------------------------------------------------|-------------------------------|
| SNP       | ref_nuc _followed by_ ref_pos _followed by_ alt_nuc (e.g. T28175C) | protein_symbol:ref_aa _followed by_ ref_pos _followed by_ alt_aa (e.g. OPG098:E162K) |
| deletion  | del:first_NT_deleted-last_NT_deleted (e.g. del:133177-133186)                        | protein_symbol:del:first_AA_deleted-last_AA_deleted (e.g. OPG197:del:34-35) |
| insertion | ref_nuc _followed by_ ref_pos _followed by_ alt_nucs (e.g. T133102TTT) | protein_symbol:ref_aa _followed by_ ref_pos _followed by_ alt_aas (e.g. OPG197:A34AK)  |

The positions refer to the reference (first nucleotide in the genome is position 1). Using the option `--profile`, multiple variant definitions can be combined into a nucleotide, amino acid or mixed profile, which means that matching genomes must have all those variations in common. In contrast, alternative variations can be defined by multiple `--profile` options. As an example, `--profile OPG044:L29P MPXV-UK_P2-006:I64K` matches genomes having the `L29P` **AND** `I64K` variation from both `NC_063383.1` and `MT903344.1` reference.

 While `--profile OPG044:L29P --profile OPG105:Q284P` (seperate --profile) matches to genomes that share either the `OPG044:L29P` **OR** `OPG105:Q284P` variation **OR** both. Accordingly, using the option **^** profiles can be defined that have not to be present in the matched genomes.

There are additional options to adjust the matching.

| option             | description                                                            |
|--------------------|------------------------------------------------------------------------|
| --count            | count matching genomes only                                            |
| --format {csv,tsv} | output format (default: tsv) |


> TIP 🕯️: use `sonar match -h ` to see all available arguments.

More example in match commnad;
> NOTE 🤨: The match command will default get all mutation profiles from the database regardless of reference.
```sh
# get all mutations
sonar match

# get all mutations which the sequence data were aligned with reference genome NC_063383.1
sonar match -r NC_063383.1

# --count to count the result of reference NC_063383.1
sonar match -r NC_063383.1 --count
```
> NOTE 🤨: Currently, if we run `sonar match --count`, it will count the result by sample name. This behavior will change soon.

```sh
# Combine with meta info.
# Samples are collected on first of May 2022
sonar match -r NC_063383.1 --COLLECTION_DATE 2022-05-01

# matching genomes with specific IDs
sonar match --sample ID-001 ID-001 ID-002
```

We use `^` as a **"NOT"** operator. We put it before any conditional statement to negate, exclude or filter the result.
```sh
# get sequences aligned with NC_063383.1 and was not collected on 2022-01-01.
sonar match -r NC_063383.1 --COLLECTION_DATE ^2022-05-01
```

More example in `--profile` match
```sh
# combine search: AA profile OR NT profile case
sonar match --profile OPG044:L29P --profile T28175C
# AA profile AND NT profile case
sonar match --profile OPG197:del:34-35 del:133188-133197

# exact match of X or N , we use small x for AA and small n for NT
# this will match MPXV-UK_P2-067:T607x
sonar match --profile MPXV-UK_P2-067:T607x

# this will match A17328N
sonar match --profile A173289n

# speacial case, we can combine exact match and any match in alternate postion.
sonar match  --profile A2145nN
# this will look in ('NG', 'NB', 'NT', 'NM', 'NS', 'NV', 'NA', 'NH',
# 'ND', 'NY', 'NR', 'NW', 'NK', 'NN', 'NC')

sonar match  --profile A2145C --COLLECTION_DATE 2022-05-31

```

More example; property match
```sh
# query with integer type
# by default we use = (equal) operator
sonar match  --AGE 25
# however, if we want to query with comparison operators (e.g., >, !=, <, >=, <=)
# , just add " " (double quote) around values.
sonar match  --AGE ">25"
sonar match  --AGE ">=25" "<=30"  # AND Combination: >=25 AND <=30
sonar match  --AGE "!=60"

# Seqeunce LENGTH in range
sonar match  --LENGTH  10641:10658
# 10641, 10642, 10643, .... 10658

# Date Range
# Sample were collected in 2022
sonar match  --COLLECTION_DATE 2022-01-01:2022-12-31
```
> TIP 🕯️: Don't forget `sonar list-prop ` to list all properties

**Export to CSV/TSV file**

pathoSonar can return results in different formats: `--format ["csv", "tsv"]`

```sh
# example command
sonar match --format tsv -o out.csv

# in csv format
sonar match --profile G3120A --COLLECTION_DATE 2022-05-31 --format csv -o out.csv

```

> NOTE 📌: accessions.txt has to contain one ID per line.

By default, pathoSonar returns every property to the output file if a user needs to export only some particular column. We can use `--out-column` tag to include only a specific property/column.

for example,

```sh
# only NUC_PROFILE,AA_PROFILE and LINEAGE will save into tsv file
sonar match  --COLLECTION_DATE 2022-06-01  -o test.tsv --out-column NUC_PROFILE,AA_PROFILE,COLLECTION_DATE
# column name separated by comma
```

### 2.6 Show infos about the used sonar system and database (info command)

Detailed infos about the used sonar system (e.g. version, reference,  number of imported genomes, unique sequences).

```sh
sonar info
```

### 2.7 Restore genome sequences from the database (restore command)
Genome sequences can be restored from the database based on their accessions.
The restored sequences are combined with their original FASTA header and  shown on the screen. The screen output can be redirected to a file easily by using `>`.

```sh
# Restore genome sequences linked to reference.
sonar restore -r NC_063383.1 --sample ID_1 ID_2 > restored.fasta
# as before, 'accessions.txt' (the file has to contain one accession per line)
sonar restore -r NC_063383.1 --sample-file accessions.txt > restored.fasta
```

### 2.8 Delete sample (delete)

```sh
sonar delete --sample ID_1 ID_2 ID_3
```

### 2.9 Import annotation result from SnpEff tool (import-ann)
Note 🕯️: please see "Annotation with SNPEff" section for how to prepare input.

To import a single annotation sample, you need to specify the sonar hash and the annotation input file.
```sh
sonar import-ann --sonar-hash ON585031.1.sonar_hash --ann-input ON585031.1.tsv
```

If you have multiple annotation files to import, you can create a sample list file (e.g., sample-list.txt) that contains the paths to the annotation input files and their corresponding sonar hashes.
```sh
sonar import-ann --sample-file  sample-list.txt
```

Example of sample-list.txt file.
```
/mnt/data/ON585031.1.tsv	/mnt/data//ON585031.1.sonar_hash
/mnt/data/OQ427120.1.tsv	/mnt/data//OQ427120.1.sonar_hash
/mnt/data/ON755244.1.tsv	/mnt/data//ON755244.1.sonar_hash
```
---------------------------------

## Additional features.

### 1. Annotation with SNPEff
This section provides guidance on preparing the input files for annotation by using SnpEff, which can then import the results into the sonar database using the "import-ann" command.

#### -- Install SNPEff and custom database

Download and installing SnpEff: it pretty easy, take a look at the [download page](https://pcingola.github.io/SnpEff/download/). SnpEff requires that you have Java v1.8 or later installed.

Configure SnpEff: Open the snpEff.config file, which is located in your SnpEff installation directory. Inside the file, you will find various configuration options. Look for the data.dir parameter and specify the path where you want to store the SnpEff databases.

For example, if you want to store the databases in the /mnt/data/ directory,
```sh
# example
data.dir = /mnt/data/
```
Obtain the reference genome: This command fetches the required data from the NCBI and generates the necessary database files for annotation.
```sh
./snpEff/scripts/buildDbNcbi.sh <genome accesion number>
# example
./snpEff/scripts/buildDbNcbi.sh NC_063383.1
```

#### -- Annotate varinat & Prepare Input for pathoSonar ('import-ann' commaad)
Here's an overview of the steps involved in preparing the input and then import back to database.

Prepare the variant input file: We use match command to generate VCF format  along with the associated `.sonar_hash`
```sh
sonar match -r ON563414.3 --sample ON585031.1  --format vcf -o ON585031.1.vcf
```

Run SnpEff annotation: Execute the SnpEff annotation command, specifying the built SnpEff database and the variant input file. SnpEff will process the variants and annotate them with functional information based on the reference genome and available annotations.
```sh
java -jar snpEff/snpEff.jar -v -stats ON585031.1.html ON563414.3 ON585031.1.vcf > ON585031.1.ann.vcf
```
the variant input file ON585031.1.vcf, and saves the annotated output in VCF format as ON585031.1.ann.vcf.

Extract the annotation output: After running SnpEff annotation, we will obtain an annotation output file in TSV format.
```sh
java -jar snpEff/SnpSift.jar extractFields -s "," -e "."  ON585031.1.ann.vcf  "CHROM" "POS" "REF" "ALT" "ANN[*].EFFECT" "ANN[*].IMPACT" > ON585031.1.tsv
```
This command extracts specific fields such as chromosome, position, reference allele, alternate allele, effect, and impact from the annotated VCF file and saves them as a TSV file named ON585031.1.tsv.

Import annotation data into Sonar: Once you have completed above steps and obtained the SnpEff annotation output file (e.g., ON585031.1.tsv in the provided example), you can use the Sonar "import-ann" command to import this annotation data into Sonar database.
```sh
sonar import-ann --sonar-hash ON585031.1.sonar_hash --ann-input ON585031.1.tsv
```

Visit https://pcingola.github.io/SnpEff/se_running/ for more information.

### 2. NCBI Downloader.
We provide the simple script to download MonkeyPox data from NCBI server.

In ".env file, please setup "NCBI API key".
```
# To get API key https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/
NCBI_API_KEY=""
NCBI_TOOL=""
NCBI_EMAIL=""
```

To run.
```sh
# example
python NCBI.downloader.py -o /mnt/data/2022-05-01/
```
In the example command, the output will be in the "2022-05-01" folder, and then two folders are created under this folder.
The first is "GB", which stores all downloaded Genbank files. The second one is output, where the final outputs are stored.

The script has to connect with the database to check if a sample is already in the database; otherwise, it will download only a new sample.

## Contact

For business inquiries or professional support requests 🍺 please contact [Dr. Stephan Fuchs](https://www.rki.de/SharedDocs/Personen/Mitarbeiter/F/Fuchs_Stephan.html)
