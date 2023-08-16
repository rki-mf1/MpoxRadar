/*
This sql script is for MariaDB/MySQL
Version: 1
----
TODO:
Recheck the format again.
Some fields might need to recheck or edited in the future to keep them optimised.
More strategies for reducing database size.
*/
CREATE DATABASE IF NOT EXISTS `mpx` CHARACTER SET utf8 COLLATE utf8_general_ci;
-- structure for table mpx.translation
CREATE TABLE IF NOT EXISTS `mpx`.`translation` (
	id INTEGER NOT NULL,
	codon VARCHAR(100) NOT NULL,
	aa VARCHAR(100) NOT NULL,
	PRIMARY KEY(id, codon)
);
-- structure for table mpx.reference
CREATE TABLE IF NOT EXISTS `mpx`.`reference` (
	id INTEGER AUTO_INCREMENT,
	accession VARCHAR(100) NOT NULL UNIQUE,
	`description` TEXT,
	organism VARCHAR(100),
	translation_id INTEGER NOT NULL,
	standard INTEGER NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(translation_id) REFERENCES translation(id) ON DELETE CASCADE
);
-- structure for table mpx.molecule
CREATE TABLE IF NOT EXISTS `mpx`.`molecule` (
	id INTEGER AUTO_INCREMENT,
	reference_id INTEGER NOT NULL,
	`type` VARCHAR(100) NOT NULL,
	accession VARCHAR(100) NOT NULL UNIQUE,
	`symbol` VARCHAR(100) NOT NULL,
	`description` VARCHAR(500) NOT NULL,
	`length` INTEGER NOT NULL,
	segment INTEGER NOT NULL,
	standard INTEGER NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(reference_id) REFERENCES reference(id) ON DELETE CASCADE
);
-- structure for table test.mpx.element
-- accession VARCHAR(100) NOT NULL UNIQUE,
CREATE TABLE IF NOT EXISTS `mpx`.`element` (
	id INTEGER AUTO_INCREMENT,
	molecule_id INTEGER NOT NULL,
	`type` VARCHAR(100) NOT NULL,
	accession VARCHAR(100) NOT NULL,
	`symbol` VARCHAR(100) NOT NULL,
	`description` TEXT NOT NULL,
	`start` INTEGER NOT NULL,
	`end` INTEGER NOT NULL,
	strand INTEGER,
	`sequence` LONGTEXT,
	standard INTEGER NOT NULL,
	parent_id INTEGER,
	PRIMARY KEY(id),
	FOREIGN KEY(molecule_id) REFERENCES molecule(id) ON DELETE CASCADE
);
-- structure for table mpx.elempart
CREATE TABLE IF NOT EXISTS `mpx`.`elempart` (
	element_id INTEGER NOT NULL,
	`start` INTEGER NOT NULL,
	`end` INTEGER NOT NULL,
	strand INTEGER NOT NULL,
	base FLOAT NOT NULL,
	segment INTEGER NOT NULL,
	PRIMARY KEY(element_id, segment),
	FOREIGN KEY(element_id) REFERENCES element(id) ON DELETE CASCADE
);
-- structure for table mpx.sequence
CREATE TABLE IF NOT EXISTS `mpx`.`sequence` (
	seqhash VARCHAR(200),
	PRIMARY KEY(seqhash)
);
-- structure for table mpx.sample
CREATE TABLE IF NOT EXISTS `mpx`.`sample` (
	id INTEGER AUTO_INCREMENT,
	`name` VARCHAR(1000) NOT NULL UNIQUE,
	seqhash VARCHAR(200) NOT NULL,
	datahash VARCHAR(200) NOT NULL,
	PRIMARY KEY(id),
	FOREIGN KEY(seqhash) REFERENCES sequence(seqhash) ON DELETE CASCADE
);
-- structure for table mpx.alignment
CREATE TABLE IF NOT EXISTS `mpx`.`alignment` (
	id INTEGER AUTO_INCREMENT,
	seqhash VARCHAR(200) NOT NULL,
	element_id INTEGER NOT NULL,
	PRIMARY KEY(id),
	FOREIGN KEY(seqhash) REFERENCES `sequence`(seqhash) ON DELETE CASCADE,
	FOREIGN KEY(element_id) REFERENCES `element`(id) ON DELETE CASCADE,
	CONSTRAINT uni_seq_eleID UNIQUE (seqhash,element_id)
);
-- structure for table test.mpx.property
CREATE TABLE IF NOT EXISTS `mpx`.`property` (
	id INTEGER AUTO_INCREMENT,
	`name` VARCHAR(200) NOT NULL UNIQUE,
	datatype VARCHAR(45) NOT NULL,
	querytype VARCHAR(45) NOT NULL,
	`description` TEXT NOT NULL,
	`standard` VARCHAR(45),
	PRIMARY KEY(id)
);
-- structure for table mpx.sample2property
CREATE TABLE IF NOT EXISTS `mpx`.`sample2property` (
	property_id INTEGER NOT NULL,
	sample_id INTEGER NOT NULL,
	value_integer INTEGER,
	value_float NUMERIC,
	value_text TEXT,
	value_varchar VARCHAR(4000),
	value_blob BLOB,
	value_date DATE,
	value_zip TEXT,
	PRIMARY KEY(property_id, sample_id),
	FOREIGN KEY(sample_id) REFERENCES `sample`(id) ON DELETE CASCADE,
	FOREIGN KEY(property_id) REFERENCES `property`(id) ON DELETE CASCADE
);
-- structure for table mpx.variant
CREATE TABLE IF NOT EXISTS `mpx`.`variant` (
	id INTEGER AUTO_INCREMENT,
	element_id INTEGER NOT NULL,
	ref VARCHAR(200) NOT NULL,
	alt VARCHAR(200) NOT NULL,
	`start` INTEGER NOT NULL,
	`end` INTEGER NOT NULL,
	parent_id INTEGER,
	label TEXT NOT NULL,
	PRIMARY KEY(id),
	UNIQUE(element_id, `start`, `end`, ref, alt),
	FOREIGN KEY(element_id) REFERENCES `element`(id) ON DELETE CASCADE
);
-- structure for table mpx.alignment2variant
CREATE TABLE IF NOT EXISTS `mpx`.`alignment2variant` (
	alignment_id INTEGER NOT NULL,
	variant_id INTEGER NOT NULL,
	PRIMARY KEY(variant_id, alignment_id),
	FOREIGN KEY(alignment_id) REFERENCES `alignment`(id) ON DELETE CASCADE,
	FOREIGN KEY(variant_id) REFERENCES variant(id) ON DELETE CASCADE
);
-- structure for table mpx.lineages
CREATE TABLE IF NOT EXISTS `mpx`.`lineages`(
	`lineage` VARCHAR(100) NOT NULL,
	`sublineage` TEXT, PRIMARY KEY(lineage)
);
-- Function Table
CREATE FUNCTION IF NOT EXISTS `mpx`.DB_VERSION() RETURNS INTEGER RETURN 1;
-- VIEW Table
DROP VIEW IF EXISTS `mpx`.`referenceView`;
CREATE VIEW `mpx`.`referenceView` AS
SELECT
	`reference`.id AS "reference.id",
	`reference`.accession AS "reference.accession",
	`reference`.`description` AS "reference.description",
	`reference`.organism AS "reference.organism",
	`reference`.standard AS "reference.standard",
	`reference`.translation_id AS "translation.id",
	molecule.id AS "molecule.id",
	molecule.`type` AS "molecule.type",
	molecule.accession AS "molecule.accession",
	molecule.symbol AS "molecule.symbol",
	molecule.`description` AS "molecule.description",
	molecule.`length` AS "molecule.length",
	molecule.segment AS "molecule.segment",
	molecule.standard AS "molecule.standard",
	element.id AS "element.id",
	element.type AS "element.type",
	element.accession AS "element.accession",
	element.symbol AS "element.symbol",
	element.description AS "element.description",
	element.start AS "element.start",
	element.`end` AS "element.end",
	element.strand AS "element.strand",
	element.sequence AS "element.sequence",
	elempart.`start` AS "elempart.start",
	elempart.`end` AS "elempart.end",
	elempart.strand AS "elempart.strand",
	elempart.segment AS "elempart.segment"
FROM
	`mpx`.reference
LEFT JOIN `mpx`.molecule ON reference.id = molecule.reference_id
LEFT JOIN `mpx`.element ON molecule.id = element.molecule_id
LEFT JOIN `mpx`.elempart ON element.id = elempart.element_id;

DROP VIEW IF EXISTS `mpx`.`sequenceView`;
CREATE VIEW `mpx`.sequenceView AS
SELECT
	sample.id AS "sample.id",
	sample.name AS "sample.name",
	sample.seqhash AS "sample.seqhash"
FROM
	`mpx`.`sample`;

DROP VIEW IF EXISTS `mpx`.`variantView`;
CREATE VIEW `mpx`.variantView AS
SELECT
 sample.id AS "sample.id",
 sample.name AS "sample.name",
 sample.seqhash AS "sample.seqhash",
 reference.id AS "reference.id",
 reference.accession AS "reference.accession",
 reference.standard AS "reference.standard",
 molecule.id AS "molecule.id",
 molecule.accession AS "molecule.accession",
 molecule.symbol AS "molecule.symbol",
 molecule.standard AS "molecule.standard",
 element.id AS "element.id",
 element.accession AS "element.accession",
 element.symbol AS "element.symbol",
 element.standard AS "element.standard",
 element.type AS "element.type",
 variant.id AS "variant.id",
 variant.ref AS "variant.ref",
 variant.start AS "variant.start",
 variant.end AS "variant.end",
 variant.alt AS "variant.alt",
	variant.label AS "variant.label",
 variant.parent_id AS "variant.parent_id"
FROM
	`mpx`.`sample`
LEFT JOIN `mpx`.sequence ON sample.seqhash = sequence.seqhash
LEFT JOIN `mpx`.alignment ON sequence.seqhash = alignment.seqhash
LEFT JOIN `mpx`.alignment2variant ON alignment.id = alignment2variant.alignment_id
LEFT JOIN `mpx`.variant ON alignment2variant.variant_id = variant.id
LEFT JOIN `mpx`.element ON variant.element_id = element.id
LEFT JOIN `mpx`.molecule ON element.molecule_id = molecule.id
LEFT JOIN `mpx`.reference ON molecule.reference_id = reference.id;

DROP VIEW IF EXISTS `mpx`.`propertyView`;
CREATE VIEW `mpx`.propertyView AS
SELECT
	sample.id AS "sample.id",
	sample.name AS "sample.name",
	property.id AS "property.id",
	property.name AS "property.name",
	property.querytype AS "propery.querytype",
	property.datatype AS "property.datatype",
	property.standard AS "property.standard",
	sample2property.value_integer AS "value_integer",
	sample2property.value_float AS "value_float",
	sample2property.value_text AS "value_text",
	sample2property.value_zip AS "value_zip",
	sample2property.value_varchar AS "value_varchar",
	sample2property.value_blob AS "value_blob",
	sample2property.value_date AS "value_date"
FROM
	`mpx`.`sample`
LEFT JOIN `mpx`.sample2property ON sample.id = sample2property.sample_id
LEFT JOIN `mpx`.property ON sample2property.property_id = property.id;

DROP VIEW IF EXISTS `mpx`.`alignmentView`;
CREATE VIEW `mpx`.`alignmentView` AS
SELECT
	sample.id AS "sample.id",
	sample.name AS "sample.name",
	sample.seqhash AS "sample.seqhash",
	alignment.id AS "alignment.id",
	reference.id AS "reference.id",
	reference.accession AS "reference.accession",
	reference.description AS "reference.description",
	reference.organism AS "reference.organism",
	reference.standard AS "reference.standard",
	reference.translation_id AS "translation.id",
	molecule.id AS "molecule.id",
	molecule.type AS "molecule.type",
	molecule.accession AS "molecule.accession",
	molecule.symbol AS "molecule.symbol",
	molecule.description AS "molecule.description",
	molecule.length AS "molecule.length",
	molecule.segment AS "molecule.segment",
	molecule.standard AS "molecule.standard",
	element.id AS "element.id",
	element.type AS "element.type",
	element.accession AS "element.accession",
	element.symbol AS "element.symbol",
	element.description AS "element.description",
	element.start AS "element.end",
	element.strand AS "element.strand",
	element.sequence AS "element.sequence"
FROM
	`mpx`.`sample`
LEFT JOIN `mpx`.alignment ON sample.seqhash = alignment.seqhash
LEFT JOIN `mpx`.element ON alignment.element_id = element.id
LEFT JOIN `mpx`.molecule ON element.molecule_id = molecule.id
LEFT JOIN `mpx`.reference ON molecule.reference_id = reference.id;
