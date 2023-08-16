from abc import ABC, abstractmethod
from dataclasses import dataclass

# Abstract class to handle Database calls.
# Implementations will be specific to the APIs used.


@dataclass
class MutationFrequency:
    symbol: str
    variant: str
    count: int


class DataFetcher(ABC):
    @abstractmethod
    def get_all_unique_samples(self):
        pass

    @abstractmethod
    def get_all_seqtech(self, filters={}) -> dict[str, list[str]]:
        pass

    @abstractmethod
    def get_all_country(self, filters={}) -> dict[str, list[str]]:
        pass

    @abstractmethod
    def get_references(self) -> dict:
        pass

    @abstractmethod
    def get_high_mutation(self):
        pass

    @abstractmethod
    def get_newest_samples(self):
        pass

    @abstractmethod
    def get_top3_country(self):
        pass

    @abstractmethod
    def count_unique_mut_ref(self):
        pass

    @abstractmethod
    def calculate_tri_mutation_sig(self):
        pass

    @abstractmethod
    def calculate_mutation_sig(self):
        pass

    @abstractmethod
    def create_snp_table(self):
        pass

    @abstractmethod
    def get_genes(self, filters={}):
        pass

    @abstractmethod
    def get_colour_map_gene(self, reference):
        pass

    @abstractmethod
    def get_distinct_genes(self, filters={}) -> dict[str, list[str]]:
        pass

    @abstractmethod
    def get_start_reference_id(self):
        pass

    @abstractmethod
    def get_property_dates(self) -> dict[str, list[str]]:
        pass

    @abstractmethod
    def get_distinct_symbols(self):
        pass

    @abstractmethod
    def get_mutation_frequency(self, query) -> list[MutationFrequency]:
        pass

    # temp

    @abstractmethod
    def get_variants_view_filtered(self):
        pass
