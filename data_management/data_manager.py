from dataclasses import dataclass
from datetime import date, datetime
import os, logging
from urllib.parse import urlparse
from uuid import uuid4
from celery import Celery
import redis
import pandas as pd
import sys, time

from .data_fetcher import DataFetcher, MutationFrequency
from flask_caching import Cache
from config import redis_config
from dash import CeleryManager, DiskcacheManager, html
from dash.long_callback.managers import BaseLongCallbackManager
from dash.long_callback import CeleryLongCallbackManager
from util.libs.mpxsonar.src.mpxsonar.dbm import sonarDBManager
from util.libs.mpxsonar.src.mpxsonar.basics import sonarBasics

instance = None


@dataclass
class ColoredMutationFrequency:
    label: html.Span
    value: str

    def options_dict(self):
        return {
            "label": self.label,
            "value": self.value,
        }


class DataManager:
    # TODO-jule - try to avoid singleton pattern
    @staticmethod
    def get_instance():
        global instance
        if instance is None:
            instance = DataManager()
        return instance

    def __init__(self):
        self.data_fetcher: DataFetcher
        self.background_callback_manager: BaseLongCallbackManager | None = None
        self.background_manager: BaseLongCallbackManager | None = None
        self.launch_uid = uuid4()
        self._initialize_cache()
        self._initialize_callback_managers()
        self._initialize_data_fetcher()

    def _initialize_cache(self):
        if "REDIS_URL" in os.environ:
            logging.info("Use Redis & Celery")
            REDIS_BACKEND_URL = os.path.join(
                os.getenv("REDIS_URL"), os.getenv("REDIS_DB_BACKEND")
            )
            from celery import Celery  # type: ignore

            # Redis server
            try:
                __uri = urlparse(REDIS_BACKEND_URL)
                db_user = __uri.username
                db_pass = __uri.password
                db_url = __uri.hostname
                db_port = __uri.port
                db_database = __uri.path.replace("/", "")
                pool = redis.ConnectionPool(host=db_url, port=db_port, db=db_database)
                redis_manager = redis.Redis(connection_pool=pool)
            except (ConnectionError, TimeoutError, ValueError) as e:
                redis_manager = None
                logging.error(f"Error connecting to Redis: {e}")
                logging.warn("No Redis system is used")
                # sys.exit(1)

            self.cache = Cache(
                config=redis_config(db_url, db_port, db_database, db_pass, db_user)
            )

        else:
            # Diskcache for non-production apps when developing locally
            logging.info("Diskcache")
            logging.warning("Diskcache for non-production apps")
            import diskcache  # type: ignore

            cache = diskcache.Cache("/tmp/.mpoxradar_cache")
            self.background_callback_manager = DiskcacheManager(
                cache, expire=200, cache_by=[lambda: self.launch_uid]
            )

    def _initialize_callback_managers(self):
        if "REDIS_URL" in os.environ:
            REDIS_BROKER_URL = os.path.join(
                os.getenv("REDIS_URL"), os.getenv("REDIS_DB_BROKER")
            )
            celery_app = Celery(
                __name__, broker=REDIS_BROKER_URL, backend=REDIS_BROKER_URL, expire=300
            )
            self.background_manager = CeleryManager(
                celery_app, cache_by=[lambda: self.launch_uid]
            )
            self.background_callback_manager = CeleryLongCallbackManager(
                celery_app, expire=300
            )

    def _initialize_data_fetcher(self):
        # django api
        if "REST_IMPLEMENTATION" in os.environ:
            from .api.django.django_api import DjangoAPI

            self.data_fetcher = DjangoAPI()

    def get_freq_mutation(args):
        with sonarDBManager(args.db, readonly=False) as dbm:
            cursor = dbm.our_match()
            df = pd.DataFrame(cursor)
            print(df)

    def match_controller(args):  # noqa: C901
        props = {}
        reserved_props = {}

        with sonarDBManager(args.db, readonly=False, debug=args.debug) as dbm:
            if args.reference:
                if len(dbm.references) != 0 and args.reference not in [
                    d["accession"] for d in dbm.references
                ]:
                    return f"{args.reference} reference is not available."
            for pname in dbm.properties:
                if hasattr(args, pname):
                    props[pname] = getattr(args, pname)
            # check column output and property name
            if args.out_column != "all":
                out_column = args.out_column.strip()
                out_column_list = out_column.split(",")
                check = all(item in dbm.properties for item in out_column_list)
                if check:
                    # sample.name is fixed
                    valid_output_column = out_column_list + ["sample.name"]
                else:
                    sys.exit(
                        "input error: "
                        + str(out_column_list)
                        + " one or more given name mismatch the available properties"
                    )
            else:
                valid_output_column = "all"
        # for reserved keywords
        reserved_key = ["sample"]
        for pname in reserved_key:
            if hasattr(args, pname):
                if pname == "sample" and len(getattr(args, pname)) > 0:
                    # reserved_props[pname] = set([x.strip() for x in args.sample])
                    reserved_props = sonarBasics.set_key(
                        reserved_props, pname, getattr(args, pname)
                    )
                # reserved_props[pname] = getattr(args, pname)
        format = "count" if args.count else args.format
        # print(props)
        output = sonarBasicsChild.match(
            args.db,
            args.profile,
            reserved_props,
            props,
            outfile=args.out,
            output_column=valid_output_column,
            debug=args.debug,
            format=format,
            showNX=args.showNX,
            reference=args.reference,
        )

        return output

    def get_references(self):
        return [r["accession"] for r in self.data_fetcher.get_references()]

    def get_all_seqtech(self, filters={}) -> list[str]:
        return self.data_fetcher.get_all_seqtech(filters)["sequencing_techs"]

    def get_all_country(self, filters={}) -> list[str]:
        return self.data_fetcher.get_all_country(filters)["countries"]

    def get_high_mutation(self):
        return self.data_fetcher.get_high_mutation()

    def get_all_unique_samples(self):
        return self.data_fetcher.get_all_unique_samples()

    def get_newest_samples(self):
        return self.data_fetcher.get_newest_samples()

    def get_property_dates(self) -> list[date]:
        return [
            datetime.strptime(date_str, "%Y-%m-%d").date()
            for date_str in self.data_fetcher.get_property_dates()["collection_dates"]
        ]

    def get_top3_country(self):
        """
        Top 3 countries with most samples.
        """
        return self.data_fetcher.get_top3_country()

    def count_unique_mut_ref(self):
        """
        "Number of mutations", i.e., min and max of number of unique mutations
        (compared to each reference genome).
        """
        return self.data_fetcher.count_unique_mut_ref()

    def calculate_tri_mutation_sig(self):
        """
        List all 96 possible mutation types
        (e.g. A[C>A]A, A[C>A]T, etc.).
        """
        # TODO-smc move code from data_fetchers to here
        return self.data_fetcher.calculate_tri_mutation_sig()

    def calculate_mutation_sig(self):
        """
        Calculate the
        six classes of base substitution: C>A, C>G, C>T, T>A, T>C, T>G.
        """
        # TODO-smc move code from data_fetchers to here
        return self.data_fetcher.calculate_mutation_sig()

    def create_snp_table(self):  # noqa: C901
        return self.data_fetcher.create_snp_table()

    def get_genes(self, filters):
        return self.data_fetcher.get_genes(filters)

    def get_colour_map_gene(self, reference):
        """
        Input: Reference accession.
        Output: the dataframe contain unique colour mapping with gene of given REF.
        """
        return self.data_fetcher.get_colour_map_gene(reference)

    def get_distinct_genes(self, filters={}):
        return self.data_fetcher.get_distinct_genes(filters)["genes"]

    def get_start_reference_id(self):
        return self.data_fetcher.get_start_reference_id()

    def get_distinct_symbols(self):
        return self.data_fetcher.get_distinct_symbols()

    def _color_mutation_frequency(
        self, mutation_frequency: MutationFrequency, color_dict: dict
    ):
        gene = f"{mutation_frequency.symbol}:{mutation_frequency.variant}({mutation_frequency.count})"
        return ColoredMutationFrequency(
            label=html.Span(
                gene,
                style={"color": color_dict[mutation_frequency.symbol]},
            ),
            value=gene
        )

    def get_mutation_frequencies_display(
        self, query, color_dict: dict
    ) -> list[ColoredMutationFrequency]:
        return [
            self._color_mutation_frequency(d, color_dict)
            for d in self.data_fetcher.get_mutation_frequency(query)
        ]

    # temp:

    def get_variants_view_filtered(self):
        return self.data_fetcher.get_variants_view_filtered()
