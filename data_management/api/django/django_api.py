import os, requests
from attr import dataclass

instance = None


@dataclass
class DjangoAPI:
    url: str = "http://127.0.0.1:8000/mpox_sonar/"
    usr: str = "admin"
    pwd: str | None = os.environ.get("MPOX_PASSWORD")


    def _get_request(self, url, params=None):
        return requests.get(url, params=params, auth=(self.usr, self.pwd))

    def get_property_dates(self):
        return []

    def get_distinct_symbols(self) -> list[str]:
        return []

    def get_start_reference_id(self) -> int:
        return []

    def get_reference_options(
        self,
    ):
        return []

    def get_sq_tech_options(
        self,
    ):
        return []

    def get_distinct_genes(
        self,
    ):
        return []

    def get_distinct_countries(
        self,
    ):
        return []

    def get_variants_view_filtered(self, filters):
        return []
    
    def get_genes(self, filters) -> list[tuple]:
        url = self.url + "genes/"
        response = self._get_request(url, params=filters)
        return response.json()["results"]

    """
    SELECT `reference.accession`, `variant.ref`, `variant.alt`, `variant.start`, `variant.end` "
            "FROM  variantView "
            "WHERE (`variant.ref` = 'C' AND `variant.alt` = 'A') "
            "OR (`variant.ref` = 'C' AND `variant.alt` = 'G') "
            "OR (`variant.ref` = 'T' AND `variant.alt` = 'A') "
            "OR (`variant.ref` = 'C' AND `variant.alt` = 'T') "
            "OR (`variant.ref` = 'G' AND `variant.alt` = 'T') "
            "OR (`variant.ref` = 'G' AND `variant.alt` = 'A') "
            "OR (`variant.ref` = 'T' AND `variant.alt` = 'C') "
            "OR (`variant.ref` = 'T' AND `variant.alt` = 'G') "
            "OR (`variant.ref` = 'G' AND `variant.alt` = 'C') "
            "OR (`variant.ref` = 'A' AND `variant.alt` = 'T') "
            "OR (`variant.ref` = 'A' AND `variant.alt` = 'G') "
            "OR (`variant.ref` = 'A' AND `variant.alt` = 'C'); "
    """
    def get_raw_snp_1(self):
        url = self.url + "snp1/"
        response = self._get_request(url)
        return response.json()["results"]

    def get_mutation_signature(self, filters=None):
        url = self.url + "mutation_signature/"
        response = self._get_request(url, params=filters)
        return response.json()["results"]
    
    def count_unique_NT_Mut_Ref(self, filters=None):
        url = self.url + "count_unique_nt_mut_ref/"
        response = self._get_request(url, params=filters)
        return response.json()["results"]

    @staticmethod
    def get_instance():
        global instance
        if instance is None:
            instance = DjangoAPI()
        return instance
