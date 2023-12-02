/*
Sonar Database schema
This sql script is for MariaDB/MySQL
Version: 1.2
----
TODO:
	* dinamic database name
	* Recheck the format again.
	* Some fields need to be rechecked or edited in the future to keep them optimised.
	* More strategies for reducing database size.
*/
DROP DATABASE IF EXISTS `patho_test`;
CREATE DATABASE IF NOT EXISTS `patho_test` CHARACTER SET utf8 COLLATE utf8_general_ci;
USE `patho_test`;
-- structure for table mpx.translation
CREATE TABLE IF NOT EXISTS `translation` (
	id INTEGER NOT NULL,
	codon VARCHAR(100) NOT NULL,
	aa VARCHAR(100) NOT NULL,
	PRIMARY KEY(id, codon)
);
-- structure for table mpx.reference
CREATE TABLE IF NOT EXISTS `reference` (
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

CREATE TABLE IF NOT EXISTS `molecule` (
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
	INDEX `idx_molecule_standard` (`standard`) USING BTREE,
	FOREIGN KEY(reference_id) REFERENCES reference(id) ON DELETE CASCADE
);
-- structure for table test.mpx.element
-- accession VARCHAR(100) NOT NULL UNIQUE,
CREATE TABLE IF NOT EXISTS `element` (
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
	INDEX `idx_element_type` (`type`) USING BTREE,
	INDEX `idx_element_standard` (`standard`) USING BTREE,
	FOREIGN KEY(molecule_id) REFERENCES molecule(id) ON DELETE CASCADE
);
-- structure for table mpx.elempart
CREATE TABLE IF NOT EXISTS `elempart` (
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
CREATE TABLE IF NOT EXISTS `sequence` (
	seqhash VARCHAR(200),
	PRIMARY KEY(seqhash)
);
-- structure for table mpx.sample
CREATE TABLE IF NOT EXISTS `sample` (
	id INTEGER AUTO_INCREMENT,
	`name` VARCHAR(1000) NOT NULL UNIQUE,
	seqhash VARCHAR(200) NOT NULL,
	datahash VARCHAR(200) NOT NULL,
	PRIMARY KEY(id),
	FOREIGN KEY(seqhash) REFERENCES sequence(seqhash) ON DELETE CASCADE
);
-- structure for table mpx.alignment
CREATE TABLE IF NOT EXISTS `alignment` (
	id INTEGER AUTO_INCREMENT,
	seqhash VARCHAR(200) NOT NULL,
	element_id INTEGER NOT NULL,
	PRIMARY KEY(id),
	INDEX `idx_alignment_seqhash` (`seqhash`) USING BTREE,
	FOREIGN KEY(seqhash) REFERENCES `sequence`(seqhash) ON DELETE CASCADE,
	FOREIGN KEY(element_id) REFERENCES `element`(id) ON DELETE CASCADE,
	CONSTRAINT uni_seq_eleID UNIQUE (seqhash,element_id)
);
-- structure for table test.mpx.property
CREATE TABLE IF NOT EXISTS `property` (
	id INTEGER AUTO_INCREMENT,
	`name` VARCHAR(200) NOT NULL UNIQUE,
	datatype VARCHAR(45) NOT NULL,
	querytype VARCHAR(45) NOT NULL,
	`description` TEXT NOT NULL,
	`target` VARCHAR(45) NOT NULL,
	`standard` VARCHAR(45),
	PRIMARY KEY(id)
);
-- structure for table mpx.sample2property
CREATE TABLE IF NOT EXISTS `sample2property` (
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
CREATE TABLE IF NOT EXISTS `variant` (
	id INTEGER AUTO_INCREMENT,
	element_id INTEGER NOT NULL,
	`pre_ref` VARCHAR(1) NULL DEFAULT NULL COLLATE 'utf8mb3_general_ci',
	ref TEXT NOT NULL,
	alt TEXT NOT NULL,
	`start` INTEGER NOT NULL,
	`end` INTEGER NOT NULL,
	parent_id INTEGER,
	label TEXT NOT NULL,
	frameshift INTEGER NOT NULL,
	PRIMARY KEY(id),
	-- # Change VARCHAR to TEXT, if we choose VARCAHR(200)
	-- # Then (errno: 150 "Foreign key constraint is incorrectly formed")
	-- UNIQUE(element_id, `start`, `end`, ref, alt),
	INDEX `idx_variant_element_frameshift` (`frameshift`) USING BTREE,
	INDEX `idx_variant_element_start` (`start`) USING BTREE,
	INDEX `idx_variant_element_pre_ref` (`pre_ref`) USING BTREE,
	FOREIGN KEY(element_id) REFERENCES `element`(id) ON DELETE CASCADE
);

-- structure for table mpx.variant2property
CREATE TABLE IF NOT EXISTS `variant2property` (
	property_id INTEGER NOT NULL,
	variant_id  INTEGER NOT NULL,
	value_integer INTEGER,
	value_float NUMERIC,
	value_text TEXT,
	value_varchar VARCHAR(4000),
	value_blob BLOB,
	value_date DATE,
	value_zip TEXT,
	PRIMARY KEY(property_id, variant_id),
	FOREIGN KEY(variant_id) REFERENCES `variant`(id) ON DELETE CASCADE,
	FOREIGN KEY(property_id) REFERENCES `property`(id) ON DELETE CASCADE
);

-- structure for table mpx.alignment2variant
CREATE TABLE IF NOT EXISTS `alignment2variant` (
	alignment_id INTEGER NOT NULL,
	variant_id INTEGER NOT NULL,
	PRIMARY KEY(variant_id, alignment_id),
	FOREIGN KEY(alignment_id) REFERENCES `alignment`(id) ON DELETE CASCADE,
	FOREIGN KEY(variant_id) REFERENCES variant(id) ON DELETE CASCADE
);
-- structure for table mpx.lineages
-- CREATE TABLE IF NOT EXISTS `lineages`(
--	`lineage` VARCHAR(100) NOT NULL,
--	`sublineage` TEXT, PRIMARY KEY(lineage)
-- );
-- Function Table
CREATE FUNCTION IF NOT EXISTS DB_VERSION() RETURNS FLOAT RETURN 1.2;
-- VIEW Table
DROP VIEW IF EXISTS `referenceView`;
CREATE VIEW `referenceView` AS
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
	reference
LEFT JOIN molecule ON reference.id = molecule.reference_id
LEFT JOIN element ON molecule.id = element.molecule_id
LEFT JOIN elempart ON element.id = elempart.element_id;

DROP VIEW IF EXISTS `sequenceView`;
CREATE VIEW sequenceView AS
SELECT
	sample.id AS "sample.id",
	sample.name AS "sample.name",
	sample.seqhash AS "sample.seqhash"
FROM
	`sample`;

DROP VIEW IF EXISTS `variantView`;
CREATE VIEW variantView AS
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
	variant.pre_ref AS "variant.pre_ref",
	variant.ref AS "variant.ref",
	variant.start AS "variant.start",
	variant.end AS "variant.end",
	variant.alt AS "variant.alt",
	variant.label AS "variant.label",
	variant.frameshift as "variant.frameshift",
	variant.parent_id AS "variant.parent_id",
	variant2property.property_id as "property_id",
	variant2property.value_integer as "value_integer",
	variant2property.value_float as "value_float",
	variant2property.value_text as "value_text",
	variant2property.value_zip as "value_zip",
	variant2property.value_varchar as "value_varchar",
	variant2property.value_blob as "value_blob",
	variant2property.value_date as "value_date"
FROM
	`sample`
LEFT JOIN sequence ON sample.seqhash = sequence.seqhash
LEFT JOIN alignment ON sequence.seqhash = alignment.seqhash
LEFT JOIN alignment2variant ON alignment.id = alignment2variant.alignment_id
LEFT JOIN variant ON alignment2variant.variant_id = variant.id
LEFT JOIN variant2property ON variant2property.variant_id = variant.id
LEFT JOIN element ON variant.element_id = element.id
LEFT JOIN molecule ON element.molecule_id = molecule.id
LEFT JOIN reference ON molecule.reference_id = reference.id;

DROP VIEW IF EXISTS `propertyView`;
CREATE VIEW propertyView AS
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
	`sample`
LEFT JOIN sample2property ON sample.id = sample2property.sample_id
LEFT JOIN property ON sample2property.property_id = property.id;

DROP VIEW IF EXISTS `alignmentView`;
CREATE VIEW `alignmentView` AS
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
	`sample`
LEFT JOIN alignment ON sample.seqhash = alignment.seqhash
LEFT JOIN element ON alignment.element_id = element.id
LEFT JOIN molecule ON element.molecule_id = molecule.id
LEFT JOIN reference ON molecule.reference_id = reference.id;

CREATE TABLE IF NOT EXISTS `annotation_type` (
	`id` TINYINT(4) NOT NULL AUTO_INCREMENT,
	`seq_ontology` VARCHAR(50) NULL DEFAULT NULL COLLATE 'utf8mb3_general_ci',
	`region` VARCHAR(50) NULL DEFAULT NULL COLLATE 'utf8mb3_general_ci',
	PRIMARY KEY (`id`) USING BTREE
);
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (1, 'coding_sequence_variant', 'EXON');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (2, 'chromosome', 'NONE');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (3, 'duplication', 'EXON');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (4, 'inversion', 'EXON');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (5, 'inframe_insertion', 'EXON');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (6, 'disruptive_inframe_insertion', 'EXON');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (7, 'inframe_deletion', 'EXON');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (8, 'disruptive_inframe_deletion', 'EXON');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (9, 'downstream_gene_variant', 'DOWNSTREAM');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (10, 'exon_variant', 'EXON');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (11, 'exon_loss_variant', 'EXON');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (12, 'frameshift_variant', 'EXON');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (13, 'gene_variant', 'GENE');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (14, 'feature_ablation', 'GENE');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (15, 'gene_fusion', 'GENE');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (16, 'bidirectional_gene_fusion', 'GENE');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (17, 'rearranged_at_DNA_level', 'GENE');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (18, 'intergenic_region', 'INTERGENIC');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (19, 'conserved_intergenic_variant', 'INTERGENIC');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (20, 'intragenic_variant', 'INTERGENIC');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (21, 'intron_variant', 'INTRON');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (22, 'conserved_intron_variant', 'INTRON');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (23, 'miRNA', 'MICRO_RNA');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (24, 'missense_variant', 'EXON');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (25, 'initiator_codon_variant', 'EXON');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (26, 'stop_retained_variant', 'EXON');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (27, 'protein_protein_contact', 'EXON');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (28, 'structural_interaction_variant', 'EXON');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (29, 'rare_amino_acid_variant', 'EXON');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (30, 'splice_acceptor_variant', 'SPLICE_SITE_ACCEPTOR');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (31, 'splice_donor_variant', 'SPLICE_SITE_DONOR');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (32, 'splice_region_variant', 'SPLICE_SITE_REGION');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (33, 'stop_lost', 'EXON');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (34, '5_prime_UTR_premature_start_codon_gain_variant', 'UTR_5_PRIME');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (35, 'stop_gained', 'EXON');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (36, 'synonymous_variant', 'EXON');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (37, 'start_lost', 'EXON');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (38, 'regulatory_region_variant', 'REGULATION');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (39, 'upstream_gene_variant', 'GENE');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (40, '3_prime_UTR_variant', 'UTR_3_PRIME');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (41, '3_prime_UTR_truncation_exon_loss_variant', 'UTR_3_PRIME');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (42, '5_prime_UTR_variant', 'UTR_5_PRIME');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (43, '5_prime_UTR_truncation_exon_loss_variant', 'UTR_5_PRIME');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (44, 'sequence_feature', 'EXON or NONE');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (45, 'start_retained_variant', 'EXON');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (46, 'non_coding_transcript_variant', 'EXON or NONE');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (47, 'non_coding_transcript_exon_variant', 'EXON');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (48, 'custom', 'NONE');
INSERT INTO `annotation_type` (`id`, `seq_ontology`, `region`) VALUES (49, '', 'NONE');


-- Annotation Type Table
CREATE TABLE IF NOT EXISTS `alignment2annotation` (
	`variant_id` INT(11) NOT NULL,
	`alignment_id` INT(11) NOT NULL,
	`annotation_id` TINYINT(4) NOT NULL,
	PRIMARY KEY (`variant_id`, `alignment_id`, `annotation_id`) USING BTREE,
	INDEX `alignment_id` (`alignment_id`) USING BTREE,
	INDEX `annotation_id` (`annotation_id`) USING BTREE,
	INDEX `variant_id` (`variant_id`) USING BTREE,
	CONSTRAINT `alignment_id` FOREIGN KEY (`alignment_id`) REFERENCES `alignment` (`id`) ON UPDATE CASCADE ON DELETE CASCADE,
	CONSTRAINT `annotation_id` FOREIGN KEY (`annotation_id`) REFERENCES `annotation_type` (`id`) ON UPDATE CASCADE ON DELETE CASCADE,
	CONSTRAINT `variant_id` FOREIGN KEY (`variant_id`) REFERENCES `variant` (`id`) ON UPDATE CASCADE ON DELETE CASCADE
);
