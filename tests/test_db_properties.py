import datetime


class DbProperties:
    """
    properties of test database "mpx_test_04", used for test comparisons
    """

    world_df_columns = [
        "COUNTRY",
        "COLLECTION_DATE",
        "SEQ_TECH",
        "sample_id_list",
        "variant.label",
        "number_sequences",
        "element.symbol",
        "gene:variant",
    ]

    variantView_df_source_columns = [
        "sample.id",
        "sample.name",
        "reference.id",
        "reference.accession",
        "element.symbol",
        "element.type",
        "variant.id",
        "variant.label",
    ]

    variantView_df_cds_columns = [
        "sample.id",
        "sample.name",
        "reference.id",
        "reference.accession",
        "element.symbol",
        "element.type",
        "variant.id",
        "variant.label",
        "gene:variant",
    ]

    propertyView_columns = [
        "sample.id",
        "sample.name",
        "COLLECTION_DATE",
        "COUNTRY",
        "GENOME_COMPLETENESS",
        "GEO_LOCATION",
        "HOST",
        "IMPORTED",
        "ISOLATE",
        "LENGTH",
        "RELEASE_DATE",
        "SEQ_TECH",
    ]

    source_variants = {
        "complete": {
            2: ["C11343A", "C70780T", "G74360A", "G8020A", "del:150586-150602"],
            4: ["C159772T", "G165079A", "G50051A", "del:133123"],
        },
        "partial": {
            2: ["C70780T", "G173318A", "G74360A", "del:150586-150602"],
            4: ["C159772T", "C43029T", "G165079A", "del:133123"],
        },
    }

    cds_variants = {
        "complete": {
            2: [
                "A233G",
                "C133F",
                "D25G",
                "L263F",
                "Q188F",
                "R194P",
                "R84K",
                "T22K",
                "T58K",
            ],
            4: [
                "A233G",
                "C133F",
                "D25G",
                "L263F",
                "Q188F",
                "R194P",
                "R84K",
                "T22K",
                "T58K",
            ],
        },
        "partial": {
            2: [
                "A233G",
                "D723G",
                "E121K",
                "L263F",
                "Q188F",
                "Q436P",
                "R194P",
                "R84K",
                "T22K",
            ],
            4: ["A233G", "D723G", "E121K", "Q188F", "Q436P", "R194P", "R84K", "T22K"],
        },
    }

    cds_gene_variants = {
        "complete": {
            2: {
                "OPG094:R194P",
                "OPG159:C133F",
                "OPG193:L263F",
                "OPG197:T22K",
                "OPG005:T22K",
                "OPG016:R84K",
                "OPG151:L263F",
                "OPG015:Q188F",
                "OPG197:D25G",
                "OPG113:T58K",
                "OPG193:A233G",
            },
            4: {
                "MPXV-USA_2022_MA001-186:R84K",
                "MPXV-USA_2022_MA001-171:T22K",
                "MPXV-USA_2022_MA001-096:T58K",
                "MPXV-USA_2022_MA001-143:C133F",
                "MPXV-USA_2022_MA001-184:T22K",
                "MPXV-USA_2022_MA001-171:D25G",
                "MPXV-USA_2022_MA001-077:R194P",
                "MPXV-USA_2022_MA001-134:L263F",
                "MPXV-USA_2022_MA001-169:A233G",
                "MPXV-USA_2022_MA001-187:Q188F",
            },
        },
        "partial": {
            2: {
                "OPG193:L263F",
                "OPG185:E121K",
                "OPG113:D723G",
                "OPG016:R84K",
                "OPG015:Q188F",
                "OPG094:R194P",
                "OPG151:Q436P",
                "OPG193:A233G",
                "OPG005:T22K",
            },
            4: {
                "MPXV-USA_2022_MA001-096:D723G",
                "MPXV-USA_2022_MA001-187:Q188F",
                "MPXV-USA_2022_MA001-184:T22K",
                "MPXV-USA_2022_MA001-134:Q436P",
                "MPXV-USA_2022_MA001-162:E121K",
                "MPXV-USA_2022_MA001-169:A233G",
                "MPXV-USA_2022_MA001-186:R84K",
                "MPXV-USA_2022_MA001-077:R194P",
            },
        },
    }

    variants_cds_per_country = {
        "Germany": {
            "complete": {
                2: {"Q188F", "T22K", "R84K", "D25G", "T58K", "R194P", "L263F", "C133F"},
                4: {"C133F", "Q188F", "R84K", "D25G", "R194P", "L263F", "T22K", "T58K"},
            },
            "partial": {
                2: {"R194P", "R84K", "L263F", "Q188F"},
                4: {"R194P", "Q188F", "R84K"},
            },
        },
        "USA": {
            "complete": {
                2: {"T22K", "R84K", "L263F", "A233G"},
                4: {"T22K", "R84K", "A233G"},
            },
            "partial": {
                2: {"L263F", "T22K", "E121K", "Q436P", "D723G", "A233G"},
                4: {"Q436P", "A233G", "T22K", "D723G", "E121K"},
            },
        },
        "Egypt": {
            "complete": {
                2: {"L263F"},
                4: set(),
            },
            "partial": {
                2: set(),
                4: set(),
            },
        },
    }

    gene_variants_cds_per_country = {
        "Germany": {
            "complete": {
                2: {
                    "OPG015:Q188F",
                    "OPG016:R84K",
                    "OPG094:R194P",
                    "OPG113:T58K",
                    "OPG151:L263F",
                    "OPG159:C133F",
                    "OPG193:L263F",
                    "OPG197:D25G",
                    "OPG197:T22K",
                },
                4: {
                    "MPXV-USA_2022_MA001-077:R194P",
                    "MPXV-USA_2022_MA001-096:T58K",
                    "MPXV-USA_2022_MA001-134:L263F",
                    "MPXV-USA_2022_MA001-143:C133F",
                    "MPXV-USA_2022_MA001-171:D25G",
                    "MPXV-USA_2022_MA001-171:T22K",
                    "MPXV-USA_2022_MA001-186:R84K",
                    "MPXV-USA_2022_MA001-187:Q188F",
                },
            },
            "partial": {
                2: {"OPG015:Q188F", "OPG094:R194P", "OPG193:L263F", "OPG016:R84K"},
                4: {
                    "MPXV-USA_2022_MA001-077:R194P",
                    "MPXV-USA_2022_MA001-186:R84K",
                    "MPXV-USA_2022_MA001-187:Q188F",
                },
            },
        },
        "USA": {
            "complete": {
                2: {"OPG005:T22K", "OPG193:L263F", "OPG193:A233G", "OPG016:R84K"},
                4: {
                    "MPXV-USA_2022_MA001-186:R84K",
                    "MPXV-USA_2022_MA001-184:T22K",
                    "MPXV-USA_2022_MA001-169:A233G",
                },
            },
            "partial": {
                2: {
                    "OPG113:D723G",
                    "OPG193:L263F",
                    "OPG185:E121K",
                    "OPG151:Q436P",
                    "OPG005:T22K",
                    "OPG193:A233G",
                },
                4: {
                    "MPXV-USA_2022_MA001-162:E121K",
                    "MPXV-USA_2022_MA001-184:T22K",
                    "MPXV-USA_2022_MA001-169:A233G",
                    "MPXV-USA_2022_MA001-096:D723G",
                    "MPXV-USA_2022_MA001-134:Q436P",
                },
            },
        },
        "Egypt": {
            "complete": {
                2: {"OPG193:L263F"},
                4: set(),
            },
            "partial": {
                2: set(),
                4: set(),
            },
        },
    }
    seq_techs_cds_per_country = {
        "Germany": {
            "complete": {2: {"Illumina"}, 4: {"Illumina"}},
            "partial": {2: {"Illumina"}, 4: {"Illumina"}},
        },
        "USA": {
            "complete": {
                2: {"Nanopore", "Illumina"},
                4: {"Nanopore", "Illumina"},
            },
            "partial": {2: {"Nanopore"}, 4: {"Nanopore"}},
        },
        "Egypt": {
            "complete": {
                2: {"Illumina"},
                4: set(),
            },
            "partial": {
                2: set(),
                4: set(),
            },
        },
    }

    seq_techs_propertyView_per_country = {
        "Germany": {"complete": {"Illumina"}, "partial": {"Illumina"}},
        "USA": {"complete": {"Nanopore", "Illumina"}, "partial": {"Nanopore"}},
        "Egypt": {
            "complete": {"Illumina"},
            "partial": set(),
        },
    }

    genes_per_country = {
        "Germany": {
            "complete": {
                2: {
                    "OPG159",
                    "OPG015",
                    "OPG016",
                    "OPG113",
                    "OPG197",
                    "OPG193",
                    "OPG094",
                    "OPG151",
                },
                4: {
                    "MPXV-USA_2022_MA001-077",
                    "MPXV-USA_2022_MA001-096",
                    "MPXV-USA_2022_MA001-134",
                    "MPXV-USA_2022_MA001-143",
                    "MPXV-USA_2022_MA001-171",
                    "MPXV-USA_2022_MA001-186",
                    "MPXV-USA_2022_MA001-187",
                },
            },
            "partial": {
                2: {"OPG015", "OPG094", "OPG193", "OPG016"},
                4: {
                    "MPXV-USA_2022_MA001-077",
                    "MPXV-USA_2022_MA001-186",
                    "MPXV-USA_2022_MA001-187",
                },
            },
        },
        "USA": {
            "complete": {
                2: {"OPG193", "OPG016", "OPG005"},
                4: {
                    "MPXV-USA_2022_MA001-169",
                    "MPXV-USA_2022_MA001-184",
                    "MPXV-USA_2022_MA001-186",
                },
            },
            "partial": {
                2: {"OPG005", "OPG193", "OPG185", "OPG113", "OPG151"},
                4: {
                    "MPXV-USA_2022_MA001-096",
                    "MPXV-USA_2022_MA001-134",
                    "MPXV-USA_2022_MA001-162",
                    "MPXV-USA_2022_MA001-169",
                    "MPXV-USA_2022_MA001-184",
                },
            },
        },
        "Egypt": {
            "complete": {
                2: {"OPG193"},
                4: set(),
            },
            "partial": {
                2: set(),
                4: set(),
            },
        },
    }

    country_entries_cds_per_country = {
        "Germany": {"complete": {2: 17, 4: 13}, "partial": {2: 11, 4: 7}},
        "USA": {"complete": {2: 11, 4: 5}, "partial": {2: 30, 4: 20}},
        "Egypt": {"complete": {2: 1, 4: 0}, "partial": {2: 0, 4: 0}},
    }

    samples_dict_cds_per_country = {
        "Germany": {"complete": {2: 153, 4: 52}, "partial": {2: 47, 4: 12}},
        "USA": {"complete": {2: 8, 4: 5}, "partial": {2: 22, 4: 15}},
        "Egypt": {"complete": {2: 1, 4: 0}, "partial": {2: 0, 4: 0}},
    }

    samples_dict_propertyView_per_country = {
        "Germany": {"complete": 153, "partial": 47},
        "USA": {"complete": 8, "partial": 22},
        "Egypt": {
            "complete": 1,
            "partial": 0,
        },
    }

    correct_rows_map_df_freq = {
        2: {
            "interval1": {
                "complete": [
                    ["Germany", 153, "DEU"],
                    ["Egypt", 1, "EGY"],
                    ["USA", 8, "USA"],
                ],
                "partial": [
                    ["Germany", 200, "DEU"],
                    ["Egypt", 1, "EGY"],
                    ["USA", 30, "USA"],
                ],
            },
            "interval2": {
                "complete": [
                    ["Germany", 3, "DEU"],
                    ["Egypt", 1, "EGY"],
                ],
                "partial": [
                    ["Germany", 4, "DEU"],
                    ["Egypt", 1, "EGY"],
                ],
            },
        }
    }

    correct_rows_map_df_incr = {
        2: {
            "interval1": {
                "complete": [
                    ["Germany", 0.0323, "DEU"],
                    ["Egypt", 0.0, "EGY"],
                    ["USA", 0.0, "USA"],
                ],
                "partial": [
                    ["Germany", 0.0968, "DEU"],
                    ["Egypt", 0.0, "EGY"],
                    ["USA", 0.2081, "USA"],
                ],
            },
            "interval2": {
                "complete": [
                    ["Germany", 0.0, "DEU"],
                    ["Egypt", 0.0, "EGY"],
                ],
                "partial": [
                    ["Germany", 0.0, "DEU"],
                    ["Egypt", 0.0, "EGY"],
                ],
            },
        }
    }

    correct_rows_frequency_bar = {
        2: {
            "Germany": {
                "interval2": {
                    "complete": [
                        ["Germany", "L263F", "OPG193", 3],
                    ],
                    "partial": [
                        ["Germany", "L263F", "OPG193", 4],
                    ],
                },
                "interval1": {
                    "complete": [
                        ["Germany", "L263F", "OPG151", 1],
                        ["Germany", "L263F", "OPG193", 153],
                        ["Germany", "R84K", "OPG016", 5],
                        ["Germany", "T22K", "OPG197", 1],
                        ["Germany", "T58K", "OPG113", 1],
                    ],
                    "partial": [
                        ["Germany", "L263F", "OPG151", 1],
                        ["Germany", "L263F", "OPG193", 200],
                        ["Germany", "R84K", "OPG016", 7],
                        ["Germany", "T22K", "OPG197", 1],
                        ["Germany", "T58K", "OPG113", 1],
                    ],
                },
            },
            "USA": {
                "interval1": {
                    "complete": [
                        ["USA", "A233G", "OPG193", 1],
                        ["USA", "L263F", "OPG193", 8],
                        ["USA", "R84K", "OPG016", 2],
                    ],
                    "partial": [
                        ["USA", "A233G", "OPG193", 4],
                        ["USA", "L263F", "OPG193", 30],
                        ["USA", "R84K", "OPG016", 2],
                    ],
                },
                "interval2": {
                    "complete": [],
                    "partial": [],
                },
            },
            "Egypt": {
                "interval1": {
                    "complete": [
                        ["Egypt", "L263F", "OPG193", 1],
                    ],
                    "partial": [
                        ["Egypt", "L263F", "OPG193", 1],
                    ],
                },
                "interval2": {
                    "complete": [
                        ["Egypt", "L263F", "OPG193", 1],
                    ],
                    "partial": [
                        ["Egypt", "L263F", "OPG193", 1],
                    ],
                },
            },
        }
    }
    correct_rows_increase_df = {
        2: {
            "Germany": {
                "interval1": {
                    "complete": [
                        [
                            "Germany",
                            "L263F",
                            "OPG151",
                            [1],
                            [datetime.date(2022, 7, 1)],
                            0.0,
                        ],
                        [
                            "Germany",
                            "L263F",
                            "OPG193",
                            [72, 28, 50, 3],
                            [
                                datetime.date(2022, 7, 1),
                                datetime.date(2022, 8, 1),
                                datetime.date(2022, 9, 1),
                                datetime.date(2022, 10, 1),
                            ],
                            -0.6010,
                        ],
                        [
                            "Germany",
                            "R84K",
                            "OPG016",
                            [2, 3],
                            [datetime.date(2022, 8, 1), datetime.date(2022, 9, 1)],
                            0.0323,
                        ],
                        [
                            "Germany",
                            "T22K",
                            "OPG197",
                            [1],
                            [datetime.date(2022, 9, 1)],
                            0.0,
                        ],
                        [
                            "Germany",
                            "T58K",
                            "OPG113",
                            [1],
                            [datetime.date(2022, 9, 1)],
                            0.0,
                        ],
                    ],
                    "partial": [
                        [
                            "Germany",
                            "L263F",
                            "OPG151",
                            [1],
                            [datetime.date(2022, 7, 1)],
                            0.0,
                        ],
                        [
                            "Germany",
                            "L263F",
                            "OPG193",
                            [78, 47, 71, 4],
                            [
                                datetime.date(2022, 7, 1),
                                datetime.date(2022, 8, 1),
                                datetime.date(2022, 9, 1),
                                datetime.date(2022, 10, 1),
                            ],
                            -0.6415,
                        ],
                        [
                            "Germany",
                            "R84K",
                            "OPG016",
                            [2, 5],
                            [datetime.date(2022, 8, 1), datetime.date(2022, 9, 1)],
                            0.0968,
                        ],
                        [
                            "Germany",
                            "T22K",
                            "OPG197",
                            [1],
                            [datetime.date(2022, 9, 1)],
                            0.0,
                        ],
                        [
                            "Germany",
                            "T58K",
                            "OPG113",
                            [1],
                            [datetime.date(2022, 9, 1)],
                            0.0,
                        ],
                    ],
                },
                "interval2": {
                    "complete": [
                        [
                            "Germany",
                            "L263F",
                            "OPG193",
                            [3],
                            [datetime.date(2022, 10, 1)],
                            0.0,
                        ],
                    ],
                    "partial": [
                        [
                            "Germany",
                            "L263F",
                            "OPG193",
                            [4],
                            [datetime.date(2022, 10, 1)],
                            0.0,
                        ],
                    ],
                },
            },
            "USA": {
                "interval1": {
                    "complete": [
                        [
                            "USA",
                            "A233G",
                            "OPG193",
                            [1],
                            [datetime.date(2022, 7, 6)],
                            0.0,
                        ],
                        [
                            "USA",
                            "L263F",
                            "OPG193",
                            [2, 4, 1, 1],
                            [
                                datetime.date(2022, 6, 30),
                                datetime.date(2022, 7, 1),
                                datetime.date(2022, 7, 2),
                                datetime.date(2022, 7, 6),
                            ],
                            -0.2892,
                        ],
                        [
                            "USA",
                            "R84K",
                            "OPG016",
                            [2],
                            [datetime.date(2022, 7, 1)],
                            0.0,
                        ],
                    ],
                    "partial": [
                        [
                            "USA",
                            "A233G",
                            "OPG193",
                            [1, 1, 1, 1],
                            [
                                datetime.date(2022, 6, 28),
                                datetime.date(2022, 7, 3),
                                datetime.date(2022, 7, 5),
                                datetime.date(2022, 7, 6),
                            ],
                            0,
                        ],
                        [
                            "USA",
                            "L263F",
                            "OPG193",
                            [2, 4, 7, 2, 1, 1, 5, 6, 1, 1],
                            [
                                datetime.date(2022, 6, 28),
                                datetime.date(2022, 6, 30),
                                datetime.date(2022, 7, 1),
                                datetime.date(2022, 7, 2),
                                datetime.date(2022, 7, 3),
                                datetime.date(2022, 7, 4),
                                datetime.date(2022, 7, 5),
                                datetime.date(2022, 7, 6),
                                datetime.date(2022, 7, 9),
                                datetime.date(2022, 8, 4),
                            ],
                            -0.0697,
                        ],
                        [
                            "USA",
                            "R84K",
                            "OPG016",
                            [2],
                            [datetime.date(2022, 7, 1)],
                            0.0,
                        ],
                    ],
                },
                "interval2": {
                    "complete": [],
                    "partial": [],
                },
            },
            "Egypt": {
                "interval1": {
                    "complete": [
                        [
                            "Egypt",
                            "L263F",
                            "OPG193",
                            [1],
                            [datetime.date(2022, 9, 26)],
                            0.0,
                        ],
                    ],
                    "partial": [
                        [
                            "Egypt",
                            "L263F",
                            "OPG193",
                            [1],
                            [datetime.date(2022, 9, 26)],
                            0.0,
                        ],
                    ],
                },
                "interval2": {
                    "complete": [
                        [
                            "Egypt",
                            "L263F",
                            "OPG193",
                            [1],
                            [datetime.date(2022, 9, 26)],
                            0.0,
                        ],
                    ],
                    "partial": [
                        [
                            "Egypt",
                            "L263F",
                            "OPG193",
                            [1],
                            [datetime.date(2022, 9, 26)],
                            0.0,
                        ],
                    ],
                },
            },
        }
    }

    correct_rows_scatter_df = {
        2: {
            "Germany": {
                "interval1": {
                    "complete": [
                        ["Germany", datetime.date(2022, 7, 1), "L263F", "OPG151", 1, 3],
                        [
                            "Germany",
                            datetime.date(2022, 7, 1),
                            "L263F",
                            "OPG193",
                            72,
                            3,
                        ],
                        [
                            "Germany",
                            datetime.date(2022, 8, 1),
                            "L263F",
                            "OPG193",
                            28,
                            34,
                        ],
                        ["Germany", datetime.date(2022, 8, 1), "R84K", "OPG016", 2, 34],
                        [
                            "Germany",
                            datetime.date(2022, 9, 1),
                            "L263F",
                            "OPG193",
                            50,
                            65,
                        ],
                        ["Germany", datetime.date(2022, 9, 1), "R84K", "OPG016", 3, 65],
                        ["Germany", datetime.date(2022, 9, 1), "T22K", "OPG197", 1, 65],
                        ["Germany", datetime.date(2022, 9, 1), "T58K", "OPG113", 1, 65],
                        [
                            "Germany",
                            datetime.date(2022, 10, 1),
                            "L263F",
                            "OPG193",
                            3,
                            95,
                        ],
                    ],
                    "partial": [
                        ["Germany", datetime.date(2022, 7, 1), "L263F", "OPG151", 1, 3],
                        [
                            "Germany",
                            datetime.date(2022, 7, 1),
                            "L263F",
                            "OPG193",
                            78,
                            3,
                        ],
                        [
                            "Germany",
                            datetime.date(2022, 8, 1),
                            "L263F",
                            "OPG193",
                            47,
                            34,
                        ],
                        ["Germany", datetime.date(2022, 8, 1), "R84K", "OPG016", 2, 34],
                        [
                            "Germany",
                            datetime.date(2022, 9, 1),
                            "L263F",
                            "OPG193",
                            71,
                            65,
                        ],
                        ["Germany", datetime.date(2022, 9, 1), "R84K", "OPG016", 5, 65],
                        ["Germany", datetime.date(2022, 9, 1), "T22K", "OPG197", 1, 65],
                        ["Germany", datetime.date(2022, 9, 1), "T58K", "OPG113", 1, 65],
                        [
                            "Germany",
                            datetime.date(2022, 10, 1),
                            "L263F",
                            "OPG193",
                            4,
                            95,
                        ],
                    ],
                },
                "interval2": {
                    "complete": [
                        [
                            "Germany",
                            datetime.date(2022, 10, 1),
                            "L263F",
                            "OPG193",
                            3,
                            95,
                        ],
                    ],
                    "partial": [
                        [
                            "Germany",
                            datetime.date(2022, 10, 1),
                            "L263F",
                            "OPG193",
                            4,
                            95,
                        ],
                    ],
                },
            },
            "USA": {
                "interval1": {
                    "complete": [
                        ["USA", datetime.date(2022, 6, 30), "L263F", "OPG193", 2, 2],
                        ["USA", datetime.date(2022, 7, 1), "L263F", "OPG193", 4, 3],
                        ["USA", datetime.date(2022, 7, 1), "R84K", "OPG016", 2, 3],
                        ["USA", datetime.date(2022, 7, 2), "L263F", "OPG193", 1, 4],
                        ["USA", datetime.date(2022, 7, 6), "A233G", "OPG193", 1, 8],
                        ["USA", datetime.date(2022, 7, 6), "L263F", "OPG193", 1, 8],
                    ],
                    "partial": [
                        ["USA", datetime.date(2022, 6, 28), "A233G", "OPG193", 1, 0],
                        ["USA", datetime.date(2022, 6, 28), "L263F", "OPG193", 2, 0],
                        ["USA", datetime.date(2022, 6, 30), "L263F", "OPG193", 4, 2],
                        ["USA", datetime.date(2022, 7, 1), "L263F", "OPG193", 7, 3],
                        ["USA", datetime.date(2022, 7, 1), "R84K", "OPG016", 2, 3],
                        ["USA", datetime.date(2022, 7, 2), "L263F", "OPG193", 2, 4],
                        ["USA", datetime.date(2022, 7, 3), "A233G", "OPG193", 1, 5],
                        ["USA", datetime.date(2022, 7, 3), "L263F", "OPG193", 1, 5],
                        ["USA", datetime.date(2022, 7, 4), "L263F", "OPG193", 1, 6],
                        ["USA", datetime.date(2022, 7, 5), "A233G", "OPG193", 1, 7],
                        ["USA", datetime.date(2022, 7, 5), "L263F", "OPG193", 5, 7],
                        ["USA", datetime.date(2022, 7, 6), "A233G", "OPG193", 1, 8],
                        ["USA", datetime.date(2022, 7, 6), "L263F", "OPG193", 6, 8],
                        ["USA", datetime.date(2022, 7, 9), "L263F", "OPG193", 1, 11],
                        ["USA", datetime.date(2022, 8, 4), "L263F", "OPG193", 1, 37],
                    ],
                },
                "interval2": {
                    "complete": [
                        [
                            "USA",
                            datetime.date(2022, 10, 2),
                            "no_mutations",
                            "no_gene",
                            0,
                            96,
                        ],
                    ],
                    "partial": [
                        [
                            "USA",
                            datetime.date(2022, 10, 2),
                            "no_mutations",
                            "no_gene",
                            0,
                            96,
                        ],
                    ],
                },
            },
            "Egypt": {
                "interval1": {
                    "complete": [
                        ["Egypt", datetime.date(2022, 9, 26), "L263F", "OPG193", 1, 90],
                    ],
                    "partial": [
                        ["Egypt", datetime.date(2022, 9, 26), "L263F", "OPG193", 1, 90],
                    ],
                },
                "interval2": {
                    "complete": [
                        ["Egypt", datetime.date(2022, 9, 26), "L263F", "OPG193", 1, 90],
                    ],
                    "partial": [
                        ["Egypt", datetime.date(2022, 9, 26), "L263F", "OPG193", 1, 90],
                    ],
                },
            },
        }
    }
