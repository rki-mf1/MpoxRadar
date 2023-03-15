import datetime


class DbProperties:
    world_df_columns = ['COUNTRY', 'COLLECTION_DATE', 'SEQ_TECH', 'sample_id_list',
                        'variant.label', 'number_sequences', 'element.symbol', 'gene:variant']

    variantView_df_source_columns = ['sample.id', 'sample.name', 'reference.id', 'reference.accession',
                                     'element.symbol',
                                     'element.type', 'variant.id', 'variant.label']

    variantView_df_cds_columns = ['sample.id', 'sample.name', 'reference.id', 'reference.accession',
                                  'element.symbol',
                                  'element.type', 'variant.id', 'variant.label', 'gene:variant']

    propertyView_columns = ['sample.id', 'sample.name', 'COLLECTION_DATE', 'COUNTRY', 'GENOME_COMPLETENESS',
                            'GEO_LOCATION', 'HOST', 'IMPORTED', 'ISOLATE', 'LENGTH', 'RELEASE_DATE', 'SEQ_TECH']

    source_variants = {
        'complete':
            {
                2: ['C11343A', 'C70780T', 'G74360A', 'G8020A', 'del:150586-150602', 'del:197161-197209'],
                4: ['C159772T', 'G165079A', 'G50051A', 'del:133123'],
            },
        'partial':
            {
                2: ['C70780T', 'G173318A', 'G74360A', 'G97290A', 'del:150586-150602', 'del:197161-197209'],
                4: ['C159772T', 'C43029T', 'G165079A', 'G55179A', 'del:133123'],
            }
    }

    cds_variants = {
        'complete':
            {
                2: ['A233G', 'A433G', 'C133F', 'D1604K', 'D25G', 'I119K', 'L263F', 'L29P', 'N95K', 'Q188F', 'R194P',
                    'R84K',
                    'S288F', 'T22K', 'T58K', 'V305G'],
                4: ['A233G', 'A433G', 'C133F', 'D1604K', 'D25G', 'I119K', 'L263F', 'N95K', 'Q188F', 'R194P', 'R84K',
                    'S288F',
                    'T22K', 'T58K', 'V305G'],
            },
        'partial':
            {
                2: ['A233G', 'A433G', 'D1604K', 'D723G', 'E121K', 'I119K', 'L142P', 'L263F', 'L29P', 'Q188F',
                    'Q436P', 'R194P',
                    'R84K', 'S288F', 'T22K', 'V305G'],
                4: ['A233G', 'A433G', 'D1604K', 'D723G', 'E121K', 'I119K', 'L142P', 'Q188F', 'Q436P', 'R194P',
                    'R84K', 'S288F',
                    'T22K', 'V305G']
            }
    }

    cds_gene_variants = {
        'complete':
            {
                2: {'OPG113:T58K', 'OPG094:R194P', 'OPG164:I119K', 'OPG197:T22K', 'OPG193:A233G', 'OPG210:D1604K',
                    'OPG117:A433G', 'OPG197:D25G', 'OPG089:V305G', 'OPG189:N95K', 'OPG005:T22K', 'OPG016:R84K',
                    'OPG159:C133F', 'OPG015:Q188F', 'OPG151:L263F', 'OPG185:S288F', 'OPG044:L29P', 'OPG193:L263F'},
                4: {'MPXV-USA_2022_MA001-186:R84K', 'MPXV-USA_2022_MA001-072:V305G', 'MPXV-USA_2022_MA001-100:A433G',
                    'MPXV-USA_2022_MA001-162:S288F', 'MPXV-USA_2022_MA001-148:I119K', 'MPXV-USA_2022_MA001-171:T22K',
                    'MPXV-USA_2022_MA001-171:D25G', 'MPXV-USA_2022_MA001-143:C133F', 'MPXV-USA_2022_MA001-184:T22K',
                    'MPXV-USA_2022_MA001-169:A233G', 'MPXV-USA_2022_MA001-134:L263F', 'MPXV-USA_2022_MA001-187:Q188F',
                    'MPXV-USA_2022_MA001-077:R194P', 'MPXV-USA_2022_MA001-182:D1604K', 'MPXV-USA_2022_MA001-165:N95K',
                    'MPXV-USA_2022_MA001-096:T58K'},
            },
        'partial':
            {
                2: {'OPG094:R194P', 'OPG164:I119K', 'OPG185:E121K', 'OPG193:A233G', 'OPG210:D1604K', 'OPG117:A433G',
                    'OPG089:V305G', 'OPG005:T22K', 'OPG016:R84K', 'OPG113:D723G', 'OPG015:Q188F', 'OPG185:S288F',
                    'OPG151:Q436P', 'OPG044:L29P', 'OPG193:L263F', 'OPG044:L142P'},
                4: {'MPXV-USA_2022_MA001-096:D723G', 'MPXV-USA_2022_MA001-187:Q188F', 'MPXV-USA_2022_MA001-184:T22K',
                    'MPXV-USA_2022_MA001-134:Q436P', 'MPXV-USA_2022_MA001-182:D1604K',
                    'MPXV-USA_2022_MA001-100:A433G', 'MPXV-USA_2022_MA001-162:E121K',
                    'MPXV-USA_2022_MA001-028:L142P', 'MPXV-USA_2022_MA001-169:A233G',
                    'MPXV-USA_2022_MA001-072:V305G', 'MPXV-USA_2022_MA001-148:I119K',
                    'MPXV-USA_2022_MA001-162:S288F', 'MPXV-USA_2022_MA001-186:R84K', 'MPXV-USA_2022_MA001-077:R194P'
                    }
            }
    }

    variants_cds_per_country = {
        'Germany':
            {
                'complete': {
                    2: {'Q188F', 'S288F', 'T22K', 'R84K', 'D25G', 'T58K', 'D1604K', 'R194P', 'L263F', 'V305G', 'N95K',
                        'C133F', 'L29P'},
                    4: {'Q188F', 'S288F', 'T22K', 'R84K', 'D25G', 'T58K', 'D1604K', 'R194P', 'L263F', 'V305G', 'N95K',
                        'C133F'}
                },
                'partial': {
                    2: {'Q188F', 'S288F', 'R84K', 'L142P', 'D1604K', 'Q436P', 'R194P', 'L263F', 'V305G', 'E121K',
                        'L29P'},
                    4: {'Q188F', 'S288F', 'R84K', 'L142P', 'D1604K', 'Q436P', 'R194P', 'V305G', 'E121K'}}
            },
        "USA": {
            'complete':
                {
                    2: {'A433G', 'T22K', 'R84K', 'L263F', 'I119K', 'L29P', 'A233G'},
                    4: {'A433G', 'T22K', 'R84K', 'I119K', 'A233G'}
                },
            'partial': {
                2: {'D723G', 'A433G', 'T22K', 'S288F', 'D1604K', 'Q436P', 'E121K', 'I119K', 'L263F', 'A233G', 'L29P'},
                4: {'D723G', 'A433G', 'T22K', 'S288F', 'D1604K', 'Q436P', 'E121K', 'I119K', 'A233G'}}
        },
        "Egypt": {
            'complete': {
                2: {'L263F', 'L29P'},
                4: set(),
            },
            'partial': {
                2: set(),
                4: set(),
            }}
    }

    gene_variants_cds_per_country = {
        'Germany':
            {
                'complete': {
                    2: {'OPG094:R194P', 'OPG193:L263F', 'OPG197:D25G', 'OPG159:C133F', 'OPG197:T22K', 'OPG113:T58K',
                        'OPG185:S288F', 'OPG189:N95K', 'OPG089:V305G', 'OPG151:L263F', 'OPG016:R84K', 'OPG044:L29P',
                        'OPG015:Q188F', 'OPG210:D1604K'},
                    4: {'MPXV-USA_2022_MA001-182:D1604K', 'MPXV-USA_2022_MA001-162:S288F',
                        'MPXV-USA_2022_MA001-187:Q188F', 'MPXV-USA_2022_MA001-171:D25G', 'MPXV-USA_2022_MA001-096:T58K',
                        'MPXV-USA_2022_MA001-072:V305G', 'MPXV-USA_2022_MA001-186:R84K', 'MPXV-USA_2022_MA001-171:T22K',
                        'MPXV-USA_2022_MA001-134:L263F', 'MPXV-USA_2022_MA001-165:N95K',
                        'MPXV-USA_2022_MA001-143:C133F',
                        'MPXV-USA_2022_MA001-077:R194P'}
                },
                'partial': {
                    2: {'OPG185:S288F', 'OPG210:D1604K', 'OPG089:V305G', 'OPG193:L263F', 'OPG015:Q188F', 'OPG185:E121K',
                        'OPG094:R194P', 'OPG016:R84K', 'OPG151:Q436P', 'OPG044:L142P', 'OPG044:L29P'},
                    4: {'MPXV-USA_2022_MA001-182:D1604K', 'MPXV-USA_2022_MA001-162:S288F',
                        'MPXV-USA_2022_MA001-187:Q188F', 'MPXV-USA_2022_MA001-028:L142P',
                        'MPXV-USA_2022_MA001-162:E121K', 'MPXV-USA_2022_MA001-072:V305G',
                        'MPXV-USA_2022_MA001-186:R84K',
                        'MPXV-USA_2022_MA001-134:Q436P', 'MPXV-USA_2022_MA001-077:R194P'}
                }
            },
        "USA": {
            'complete':
                {
                    2: {'OPG005:T22K', 'OPG193:L263F', 'OPG193:A233G', 'OPG117:A433G', 'OPG164:I119K', 'OPG016:R84K',
                        'OPG044:L29P'},
                    4: {'MPXV-USA_2022_MA001-100:A433G', 'MPXV-USA_2022_MA001-148:I119K',
                        'MPXV-USA_2022_MA001-186:R84K',
                        'MPXV-USA_2022_MA001-184:T22K', 'MPXV-USA_2022_MA001-169:A233G'}
                },
            'partial': {
                2: {'OPG185:S288F', 'OPG117:A433G', 'OPG210:D1604K', 'OPG113:D723G', 'OPG193:L263F', 'OPG164:I119K',
                    'OPG185:E121K', 'OPG151:Q436P', 'OPG005:T22K', 'OPG044:L29P', 'OPG193:A233G'},
                4: {'MPXV-USA_2022_MA001-182:D1604K', 'MPXV-USA_2022_MA001-162:S288F', 'MPXV-USA_2022_MA001-100:A433G',
                    'MPXV-USA_2022_MA001-148:I119K', 'MPXV-USA_2022_MA001-162:E121K', 'MPXV-USA_2022_MA001-184:T22K',
                    'MPXV-USA_2022_MA001-169:A233G', 'MPXV-USA_2022_MA001-096:D723G', 'MPXV-USA_2022_MA001-134:Q436P'}
            }
        },
        "Egypt": {
            'complete': {
                2: {'OPG193:L263F', 'OPG044:L29P'},
                4: set(),
            },
            'partial': {
                2: set(),
                4: set(),
            }}
    }
    seq_techs_cds_per_country = {
        'Germany':
            {
                'complete': {
                    2: {'Illumina'},
                    4: {'Illumina'}
                },
                'partial': {
                    2: {'Illumina'},
                    4: {'Illumina'}
                }
            },
        "USA": {
            'complete':
                {
                    2: {'Nanopore', 'Illumina'},
                    4: {'Nanopore', 'Illumina'},
                },
            'partial':
                {
                    2: {'Nanopore'},
                    4: {'Nanopore'}
                }
        },
        "Egypt": {
            'complete':
                {
                    2: {'Illumina'},
                    4: set(),
                },
            'partial':
                {
                    2: set(),
                    4: set(),
                }
        }
    }

    seq_techs_propertyView_per_country = {
        'Germany': {
            'complete': {'Illumina'},
            'partial': {'Illumina'}
        },
        "USA": {
            'complete': {'Nanopore', 'Illumina'},
            'partial': {'Nanopore'}
        },
        "Egypt": {
            'complete': {'Illumina'},
            'partial': set(),
        }
    }

    genes_per_country = {
        'Germany':
            {
                'complete': {
                    2: {'OPG044', 'OPG185', 'OPG193', 'OPG089', 'OPG094', 'OPG159', 'OPG151', 'OPG189', 'OPG015',
                        'OPG113',
                        'OPG016', 'OPG197', 'OPG210'},
                    4: {'MPXV-USA_2022_MA001-182', 'MPXV-USA_2022_MA001-072', 'MPXV-USA_2022_MA001-171',
                        'MPXV-USA_2022_MA001-165', 'MPXV-USA_2022_MA001-187', 'MPXV-USA_2022_MA001-162',
                        'MPXV-USA_2022_MA001-143', 'MPXV-USA_2022_MA001-096', 'MPXV-USA_2022_MA001-077',
                        'MPXV-USA_2022_MA001-186', 'MPXV-USA_2022_MA001-134'}
                },
                'partial': {
                    2: {'OPG044', 'OPG185', 'OPG193', 'OPG089', 'OPG094', 'OPG151', 'OPG015', 'OPG016', 'OPG210'},
                    4: {'MPXV-USA_2022_MA001-182', 'MPXV-USA_2022_MA001-072', 'MPXV-USA_2022_MA001-187',
                        'MPXV-USA_2022_MA001-162', 'MPXV-USA_2022_MA001-077', 'MPXV-USA_2022_MA001-186',
                        'MPXV-USA_2022_MA001-134', 'MPXV-USA_2022_MA001-028'}
                }
            },
        "USA": {
            'complete':
                {
                    2: {'OPG044', 'OPG193', 'OPG117', 'OPG164', 'OPG005', 'OPG016'},
                    4: {'MPXV-USA_2022_MA001-184', 'MPXV-USA_2022_MA001-148', 'MPXV-USA_2022_MA001-169',
                        'MPXV-USA_2022_MA001-186', 'MPXV-USA_2022_MA001-100'},
                },
            'partial': {
                2: {'OPG044', 'OPG185', 'OPG193', 'OPG117', 'OPG164', 'OPG005', 'OPG151', 'OPG113', 'OPG210'},
                4: {'MPXV-USA_2022_MA001-182', 'MPXV-USA_2022_MA001-096', 'MPXV-USA_2022_MA001-184',
                    'MPXV-USA_2022_MA001-162', 'MPXV-USA_2022_MA001-148', 'MPXV-USA_2022_MA001-169',
                    'MPXV-USA_2022_MA001-134', 'MPXV-USA_2022_MA001-100'},
            }
        },
        "Egypt": {
            'complete': {
                2: {'OPG044', 'OPG193'},
                4: set(),
            },
            'partial': {
                2: set(),
                4: set(),
            }
        }
    }

    country_entries_cds_per_country = {
        'Germany':
            {
                'complete': {2: 30, 4: 22},
                'partial': {2: 25, 4: 17}
            },
        'USA':
            {
                'complete': {2: 21, 4: 7},
                'partial': {2: 62, 4: 38}
            },
        'Egypt':
            {
                'complete': {2: 2, 4: 0},
                'partial': {2: 0, 4: 0}
            }
    }

    samples_dict_cds_per_country = {
        'Germany':
            {
                'complete': {2: 222, 4: 107},
                'partial': {2: 71, 4: 34}
            },
        'USA':
            {
                'complete': {2: 12, 4: 8},
                'partial': {2: 37, 4: 30}
            },
        'Egypt':
            {
                'complete': {2: 1, 4: 0},
                'partial': {2: 0, 4: 0}
            }
    }

    samples_dict_propertyView_per_country = {
        'Germany': {
            'complete': 222,
            'partial': 71
        },
        "USA": {
            'complete': 12,
            'partial': 37
        },
        "Egypt": {
            'complete': 1,
            'partial': 0,
        }
    }

    correct_rows_map_df_freq = {
        2: {
            'interval2': {
                'complete': [
                    ['Germany', 4, 'DEU'],
                    ['Egypt', 1, 'EGY'],
                ],
                'partial': [
                    ['Germany', 6, 'DEU'],
                    ['Egypt', 1, 'EGY'],
                ]
            },
            'interval1': {
                'complete': [
                    ['Germany', 222, 'DEU'],
                    ['Egypt', 1, 'EGY'],
                    ['USA', 12, 'USA'],
                ],
                'partial': [
                    ['Germany', 293, 'DEU'],
                    ['Egypt', 1, 'EGY'],
                    ['USA', 49, 'USA'],
                ]
            },
        }
    }

    correct_rows_map_df_incr = {
        2: {
            'interval2': {
                'complete': [
                    ['Germany', 0.0, 'DEU'],
                    ['Egypt', 0.0, 'EGY'],
                ],
                'partial': [
                    ['Germany', 0.0, 'DEU'],
                    ['Egypt', 0.0, 'EGY'],
                ]
            },
            'interval1': {
                'complete': [
                    ['Germany', 0.0323, 'DEU'],
                    ['Egypt', 0.0, 'EGY'],
                    ['USA', 0.0, 'USA'],
                ],
                'partial': [
                    ['Germany', 0.0645, 'DEU'],
                    ['Egypt', 0.0, 'EGY'],
                    ['USA', 0.1156, 'USA'],
                ]
            },
        }
    }

    correct_rows_frequency_bar = {
        2: {
            'Germany': {
                'interval2': {
                    'complete': [
                        ["Germany", "L263F", "OPG193", 4], ],
                    'partial': [
                        ["Germany", "L263F", "OPG193", 6], ]

                },
                'interval1': {
                    'complete': [
                        ['Germany', 'L263F', 'OPG151', 1],
                        ['Germany', 'L263F', 'OPG193', 222],
                        ['Germany', 'R84K', 'OPG016', 5],
                        ['Germany', 'T22K', 'OPG197', 1],
                        ['Germany', 'T58K', 'OPG113', 1],
                    ],
                    'partial': [
                        ['Germany', 'L263F', 'OPG151', 1],
                        ['Germany', 'L263F', 'OPG193', 293],
                        ['Germany', 'R84K', 'OPG016', 8],
                        ['Germany', 'T22K', 'OPG197', 1],
                        ['Germany', 'T58K', 'OPG113', 1],
                    ]
                },
            },
            'USA': {
                'interval1': {
                    'complete': [
                        ['USA', 'A233G', 'OPG193', 1],
                        ['USA', 'L263F', 'OPG193', 12],
                        ['USA', 'R84K', 'OPG016', 2],
                    ],
                    'partial': [
                        ['USA', 'A233G', 'OPG193', 7],
                        ['USA', 'L263F', 'OPG193', 49],
                        ['USA', 'R84K', 'OPG016', 2],
                    ],
                },
                'interval2': {
                    'complete': [
                    ],
                    'partial': [
                    ],
                }
            },
            'Egypt': {
                'interval1': {
                    'complete': [
                        ['Egypt', 'L263F', 'OPG193', 1],
                    ],
                    'partial': [
                        ['Egypt', 'L263F', 'OPG193', 1],
                    ],
                },
                'interval2': {
                    'complete': [
                        ['Egypt', 'L263F', 'OPG193', 1],
                    ],
                    'partial': [
                        ['Egypt', 'L263F', 'OPG193', 1],
                    ],
                }
            }
        }
    }
    correct_rows_increase_df = {
        2: {
            'Germany': {

                'interval1': {
                    'complete': [
                        ['Germany', 'L263F', 'OPG151', [1], [datetime.date(2022, 7, 1)], 0.0],
                        ['Germany', 'L263F', 'OPG193', [106, 40, 72, 4], [datetime.date(2022, 7, 1),
                                                                          datetime.date(2022, 8, 1),
                                                                          datetime.date(2022, 9, 1),
                                                                          datetime.date(2022, 10, 1)], -0.8902],
                        ['Germany', 'R84K', 'OPG016', [2, 3], [datetime.date(2022, 8, 1), datetime.date(2022, 9, 1)],
                         0.0323],
                        ['Germany', 'T22K', 'OPG197', [1], [datetime.date(2022, 9, 1)], 0.0],
                        ['Germany', 'T58K', 'OPG113', [1], [datetime.date(2022, 9, 1)], 0.0],
                    ],
                    'partial': [
                        ['Germany', 'L263F', 'OPG151', [1], [datetime.date(2022, 7, 1)], 0.0],
                        ['Germany', 'L263F', 'OPG193', [118, 65, 104, 6],
                         [datetime.date(2022, 7, 1), datetime.date(2022, 8, 1), datetime.date(2022, 9, 1),
                          datetime.date(2022, 10, 1)], -0.9625],
                        ['Germany', 'R84K', 'OPG016', [3, 5], [datetime.date(2022, 8, 1), datetime.date(2022, 9, 1)],
                         0.0645],
                        ['Germany', 'T22K', 'OPG197', [1], [datetime.date(2022, 9, 1)], 0.0],
                        ['Germany', 'T58K', 'OPG113', [1], [datetime.date(2022, 9, 1)], 0.0],
                    ]
                },
                'interval2': {
                    'complete': [
                        ['Germany', 'L263F', 'OPG193', [4], [datetime.date(2022, 10, 1)], 0.0],
                    ],
                    'partial': [
                        ['Germany', 'L263F', 'OPG193', [6], [datetime.date(2022, 10, 1)], 0.0],
                    ]
                },
            },
            'USA': {
                'interval1': {
                    'complete': [
                        ['USA', 'A233G', 'OPG193', [1], [datetime.date(2022, 7, 6)], 0.0],
                        ['USA', 'L263F', 'OPG193', [2, 5, 2, 2, 1],
                         [datetime.date(2022, 6, 30), datetime.date(2022, 7, 1), datetime.date(2022, 7, 2),
                          datetime.date(2022, 7, 6), datetime.date(2022, 7, 7)], -0.268],
                        ['USA', 'R84K', 'OPG016', [2], [datetime.date(2022, 7, 1)], 0.0],
                    ],
                    'partial': [
                        ['USA', 'A233G', 'OPG193', [2, 1, 1, 1, 1, 1],
                         [datetime.date(2022, 6, 28), datetime.date(2022, 7, 1), datetime.date(2022, 7, 3),
                          datetime.date(2022, 7, 4), datetime.date(2022, 7, 5), datetime.date(2022, 7, 6)], -0.1128],
                        ['USA', 'L263F', 'OPG193', [3, 6, 9, 3, 1, 3, 8, 11, 2, 1, 1, 1],
                         [datetime.date(2022, 6, 28), datetime.date(2022, 6, 30), datetime.date(2022, 7, 1),
                          datetime.date(2022, 7, 2), datetime.date(2022, 7, 3), datetime.date(2022, 7, 4),
                          datetime.date(2022, 7, 5), datetime.date(2022, 7, 6), datetime.date(2022, 7, 7),
                          datetime.date(2022, 7, 9), datetime.date(2022, 7, 23), datetime.date(2022, 8, 4)], -0.1341],
                        ['USA', 'R84K', 'OPG016', [2], [datetime.date(2022, 7, 1)], 0.0],
                    ],
                },
                'interval2': {
                    'complete': [
                    ],
                    'partial': [
                    ],
                }
            },
            'Egypt': {
                'interval1': {
                    'complete': [
                        ['Egypt', 'L263F', 'OPG193', [1], [datetime.date(2022, 9, 26)], 0.0],
                    ],
                    'partial': [
                        ['Egypt', 'L263F', 'OPG193', [1], [datetime.date(2022, 9, 26)], 0.0],
                    ],
                },
                'interval2': {
                    'complete': [
                        ['Egypt', 'L263F', 'OPG193', [1], [datetime.date(2022, 9, 26)], 0.0],
                    ],
                    'partial': [
                        ['Egypt', 'L263F', 'OPG193', [1], [datetime.date(2022, 9, 26)], 0.0],
                    ],
                }
            }
        }
    }

    correct_rows_scatter_df = {
        2: {
            'Germany': {
                'interval1': {
                    'complete': [
                        ['Germany', datetime.date(2022, 7, 1), 'L263F', 'OPG151', 1, 3],
                        ['Germany', datetime.date(2022, 7, 1), 'L263F', 'OPG193', 106, 3],
                        ['Germany', datetime.date(2022, 8, 1), 'L263F', 'OPG193', 40, 34],
                        ['Germany', datetime.date(2022, 8, 1), 'R84K', 'OPG016', 2, 34],
                        ['Germany', datetime.date(2022, 9, 1), 'L263F', 'OPG193', 72, 65],
                        ['Germany', datetime.date(2022, 9, 1), 'R84K', 'OPG016', 3, 65],
                        ['Germany', datetime.date(2022, 9, 1), 'T22K', 'OPG197', 1, 65],
                        ['Germany', datetime.date(2022, 9, 1), 'T58K', 'OPG113', 1, 65],
                        ['Germany', datetime.date(2022, 10, 1), 'L263F', 'OPG193', 4, 95],
                    ],
                    'partial': [
                        ['Germany', datetime.date(2022, 7, 1), 'L263F', 'OPG151', 1, 3],
                        ['Germany', datetime.date(2022, 7, 1), 'L263F', 'OPG193', 118, 3],
                        ['Germany', datetime.date(2022, 8, 1), 'L263F', 'OPG193', 65, 34],
                        ['Germany', datetime.date(2022, 8, 1), 'R84K', 'OPG016', 3, 34],
                        ['Germany', datetime.date(2022, 9, 1), 'L263F', 'OPG193', 104, 65],
                        ['Germany', datetime.date(2022, 9, 1), 'R84K', 'OPG016', 5, 65],
                        ['Germany', datetime.date(2022, 9, 1), 'T22K', 'OPG197', 1, 65],
                        ['Germany', datetime.date(2022, 9, 1), 'T58K', 'OPG113', 1, 65],
                        ['Germany', datetime.date(2022, 10, 1), 'L263F', 'OPG193', 6, 95],
                    ]
                },
                'interval2': {
                    'complete': [
                        ['Germany', datetime.date(2022, 10, 1), 'L263F', 'OPG193', 4, 95],
                    ],
                    'partial': [
                        ['Germany', datetime.date(2022, 10, 1), 'L263F', 'OPG193', 6, 95],
                    ]
                },
            },
            'USA': {
                'interval1': {
                    'complete': [
                        ['USA', datetime.date(2022, 6, 30), 'L263F', 'OPG193', 2, 2],
                        ['USA', datetime.date(2022, 7, 1), 'L263F', 'OPG193', 5, 3],
                        ['USA', datetime.date(2022, 7, 1), 'R84K', 'OPG016', 2, 3],
                        ['USA', datetime.date(2022, 7, 2), 'L263F', 'OPG193', 2, 4],
                        ['USA', datetime.date(2022, 7, 6), 'A233G', 'OPG193', 1, 8],
                        ['USA', datetime.date(2022, 7, 6), 'L263F', 'OPG193', 2, 8],
                        ['USA', datetime.date(2022, 7, 7), 'L263F', 'OPG193', 1, 9],
                    ],
                    'partial': [
                        ['USA', datetime.date(2022, 6, 28), 'A233G', 'OPG193', 2, 0],
                        ['USA', datetime.date(2022, 6, 28), 'L263F', 'OPG193', 3, 0],
                        ['USA', datetime.date(2022, 6, 30), 'L263F', 'OPG193', 6, 2],
                        ['USA', datetime.date(2022, 7, 1), 'A233G', 'OPG193', 1, 3],
                        ['USA', datetime.date(2022, 7, 1), 'L263F', 'OPG193', 9, 3],
                        ['USA', datetime.date(2022, 7, 1), 'R84K', 'OPG016', 2, 3],
                        ['USA', datetime.date(2022, 7, 2), 'L263F', 'OPG193', 3, 4],
                        ['USA', datetime.date(2022, 7, 3), 'A233G', 'OPG193', 1, 5],
                        ['USA', datetime.date(2022, 7, 3), 'L263F', 'OPG193', 1, 5],
                        ['USA', datetime.date(2022, 7, 4), 'A233G', 'OPG193', 1, 6],
                        ['USA', datetime.date(2022, 7, 4), 'L263F', 'OPG193', 3, 6],
                        ['USA', datetime.date(2022, 7, 5), 'A233G', 'OPG193', 1, 7],
                        ['USA', datetime.date(2022, 7, 5), 'L263F', 'OPG193', 8, 7],
                        ['USA', datetime.date(2022, 7, 6), 'A233G', 'OPG193', 1, 8],
                        ['USA', datetime.date(2022, 7, 6), 'L263F', 'OPG193', 11, 8],
                        ['USA', datetime.date(2022, 7, 7), 'L263F', 'OPG193', 2, 9],
                        ['USA', datetime.date(2022, 7, 9), 'L263F', 'OPG193', 1, 11],
                        ['USA', datetime.date(2022, 7, 23), 'L263F', 'OPG193', 1, 25],
                        ['USA', datetime.date(2022, 8, 4), 'L263F', 'OPG193', 1, 37],
                    ],
                },
                'interval2': {
                    'complete': [
                        ['USA', datetime.date(2022, 10, 2), 'no_mutations', 'no_gene', 0, 96],
                    ],
                    'partial': [
                        ['USA', datetime.date(2022, 10, 2), 'no_mutations', 'no_gene', 0, 96],
                    ],
                }
            },
            'Egypt': {
                'interval1': {
                    'complete': [
                        ['Egypt', datetime.date(2022, 9, 26), 'L263F', 'OPG193', 1, 90],
                    ],
                    'partial': [
                        ['Egypt', datetime.date(2022, 9, 26), 'L263F', 'OPG193', 1, 90],
                    ],
                },
                'interval2': {
                    'complete': [
                        ['Egypt', datetime.date(2022, 9, 26), 'L263F', 'OPG193', 1, 90],
                    ],
                    'partial': [
                        ['Egypt', datetime.date(2022, 9, 26), 'L263F', 'OPG193', 1, 90],
                    ],
                }
            }
        }
    }
