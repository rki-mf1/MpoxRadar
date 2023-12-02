# Version 0.6.0

## Add
1.
2.
3.
4.
5. Features from MpoxSonar
6. Molecule_ID at SQL stm.
7. Multi Reference

## Change/Edit
1. Merge code from covsonar2 and MpoxSonar.
2. Datbase schema
3. VCF generated function
4. Match command, to support multi reference
5.


## Delete/Remove
1.
2. old functions that no longer used or replaced with newer function from covsonar2
3. remove SUM (covsonar version)


## Bugs
1. Accumulated bugs before recoding this file.
2. Query using date range; `--DATE_OF_SAMPLING 2021-04-01:2021-06-01` (**fixed**)
3. duplicated mutation profiles in output (**fixed**, add DISTINCT at inner FROM)
4. bugs on match, no output if using --profile X AND X (e.g.,`sonar match -r NC_063383.1 --profile OPG098:E162K OPG197:del:19-19`) (**fixed**, add SUM)
5. `sonar match -r MN908947.3 --IMPORTED 2023-01-01:2023-09-31`-> ValueError: day is out of range for month (**fixed**)
6. `sonar match -r MN908947.3 --profile S:del:69 --debug` Incorrect format because it was just only one position (correct format S:del:69-69?) (**fixed**)
7. Program raise the error when input FASTA was in invalid format! (**fixed**)

## Thought?
1. --prop A --prop Y --prop X
right now it combines different props. with OR "A OR Y OR X", what if we want "--prop A AND --prop Y"?
how we choose AND/OR, define with tag? (e.g., --prop A --prop Y --prop X --combine AND)

2. Increase Insert performance, try to apply parallel data inserts but got error
"mariadb.OperationalError: Deadlock found when trying to get lock; try restarting transaction"
during insert variant, (not sure excutemany cause the problem.)
