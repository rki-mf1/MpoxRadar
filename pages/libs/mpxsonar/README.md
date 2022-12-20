# MPoxSonar

MPoxSonar is an extension of Covsonar (the database-driven system for handling genomic sequences of SARS-CoV-2 and screening genomic profiles, developed at the RKI (https://github.com/rki-mf1/covsonar).) that adds support for multiple genome references and quick processing with MariaDB.

What's new in MPoxSonar
* New design
    * Improve workflows
    * Performance improvements
* Exciting new features
	* Support multiple genome references
* New database design
	* New database schema for MariaDB

Now, MPoxSonar is mainly used for MonkeyPox virus but it can be used with other pathogens.

## Prerequisite software

1. Install MariaDB server (MySQL should work too!, not tested yet).
2. Install conda environment.

## 1. MPoxSonar Installation.

### Stable version.🔖

None

### Dev. version.🚧

```sh
# example command
git clone https://github.com/silenus092/mpxsonar.git

conda create -n mpxsonar-dev python=3.9 poetry fortran-compiler nox pre-commit emboss=6.6.0
conda activate mpxsonar-dev  # needs to be activated for the following commands to work
cd mpxsonar
poetry install
# test
sonar -h
```

Finally, you need to copy and change name from ".env.template" file to ".env for a convenient of database connection, and then you edit the file according to your system.

## 2. Usage

In MPoxSonar, the table below shows the several commands that can be called.

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

Each tool provides a help page that can be accessed with the `-h` option.

```sh
# display help page
sonar -h
# display help page for each tool
sonar import -h
```

### 2.1 Setup database (setup ⛽)

First, we have to create a new database instance.
```sh
sonar setup
```
Or we can create a new database with a defined URL.
```sh
sonar setup --db https://super_user:123456@localhost:3306/mpx
```

> Attention ⚠️: The database name is a fixed name, namely "mpx".

> Attention ⚠️: If you already set up .env file, then there is no need to add the --db tag in the command. The rest of our example command will not include the "--db" tag. We assume there is the .env file on your system.

> Note 🕯️: By default, NC_063383.1 (Monkeypox virus, 2022) is used as a reference when running the setup command. If we want to set up a database for a different reference genome, we can add `--gbk` following the Genbank file.

### 2.2 Property management (`list-prop`, `add-prop` and `delete-prop`)

In MPoxSonar, users can now arbitrarily add meta information or properties into a database to fit a specific project objective.

To add properties, we can use the `add-prop` command to add meta information into the database.

The required arguments are listed below when we use `add-prop` command
* `--name`, name of sample property
* `--descr`, description of the new property
* `--dtype`, data type of the new property (e.g., 'integer', 'float', 'text', 'date', 'zip')

```sh
# for example
sonar add-prop --name LINEAGE --dtype text --descr "store Lineage"
#
sonar add-prop --name AGE --dtype integer --descr "age information"
#
sonar add-prop --name DATE_DRAW --dtype date --descr "sampling date"
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
>⚠️ Attention: Some references did not annotate the gene name but just gave only "locus_tag" in the GenBank file. The program will use "locus_tag" instead of the gene name when adding to the database. This annotation will affect the search (match) command for protein mutation.
For example, we want to search for the D88K mutation. The reference MT903344.1 used MPXV-UK_ as the protein ID, so when we perform the search, we will write it as "MPXV-UK_P2-076:D88K", while the NC_063383.1 use "OPG093" (e.g., OPG093:D88K).

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
sonar import --tsv meta.passed.tsv --threads 200 --cache tmp_cache --cols sample=IMS_ID

```
> NOTE 🤨: please make sure the `--cols sample=IMS_ID` is correctly referenced. If you have a different column name, please change it according to the meta-info file (for example, `--cols sample=IMS_NEW_ID`)

### 2.5 Query genome sequences based on profiles (match)

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
| --format {csv,tsv,vcf}| output format (default: tsv) |


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

```
# Combine with meta info.
# Samples are collected on first of January 2022
sonar match -r NC_063383.1 --COLLECTION_DATE 2022-01-01

# matching genomes with specific IDs
sonar match --sample ID-001 ID-001 ID-002
```

We use `^` as a **"NOT"** operator. We put it before any conditional statement to negate, exclude or filter the result.
```sh
# get sequences aligned with NC_063383.1 and was not collected on 2022-01-01.
sonar match -r NC_063383.1 --COLLECTION_DATE ^2022-01-01
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
# by default we use = operator
sonar match  --AGE 25
# however, if we want to query with comparison operators (e.g., >, !=, <, >=, <=)
# , just add " " (double quote) around values.
sonar match  --AGE ">25"
sonar match  --AGE ">=25" "<=30"  # AND Combination: >=25 AND <=30
sonar match  --AGE "!=60"

# Range query matches
sonar match  --DEMIS_ID_PC  10641:10658
# 10641, 10642, 10643, .... 10658

# Date
# Sample were collected in 2020
sonar match  --COLLECTION_DATE 2020-01-01:2020-12-31
```
> TIP 🕯️: Don't forget `sonar list-prop ` to list all properties

**Export to CSV/TSV/VCF file**

covSonar can return results in different formats: `--format ["csv", "tsv", "vcf"]`

```sh
# example command
sonar match  --format csv -o out.csv

# in vcf format
sonar match --profile A2145C --COLLECTION_DATE 2022-05-31 --format vcf -o out.vcf

# In case we have a list of ID and it is stored in a file, so we can use --sample-file
# tag to load and query according to the listed ID; example of --sample-file
sonar match --sample-file accessions.txt --format vcf -o out.vcf
```

> NOTE 📌: accessions.txt has to contain one ID per line.

By default, covSonar returns every property to the output file if a user needs to export only some particular column. We can use `--out-column` tag to include only a specific property/column.

for example,

```sh
# only NUC_PROFILE,AA_PROFILE and LINEAGE will save into tsv file
sonar match  --DATE_DRAW 2021-03-01  -o test.tsv --out-column NUC_PROFILE,AA_PROFILE,LINEAGE
# column name separated by comma
```

### 2.6 Show infos about the used sonar system and database (info)

Detailed infos about the used sonar system (e.g. version, reference,  number of imported genomes, unique sequences, available metadata).

```sh
sonar info
```

### 2.7 Restore genome sequences from the database (restore)
Genome sequences can be restored from the database based on their accessions.
The restored sequences are combined with their original FASTA header and  shown on the screen. The screen output can be redirected to a file easily by using `>`.

```sh
# Restore genome sequences linked to accessions 'mygenome1' and 'mygenome2' from the
# database 'test.db' and write these to a fasta file named 'restored.fasta'
sonar restore --sample mygenome1 mygenome2 > restored.fasta
# as before, but consider all accessions from 'accessions.txt' (the file has to
# contain one accession per line)
sonar restore --sample-file accessions.txt > restored.fasta
```

### 2.8 Delete sample (delete)

```sh
sonar delete --sample ID_1 ID_2 ID_3
```



---------------------------------

## Contact

For business inquiries or professional support requests 🍺 please contact [Dr. Stephan Fuchs](https://www.rki.de/SharedDocs/Personen/Mitarbeiter/F/Fuchs_Stephan.html)
