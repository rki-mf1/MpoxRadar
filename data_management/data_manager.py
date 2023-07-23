from typing import Any
from .data_fetcher import DataFetcher
import os


class DataManager:

    def __init__(self):
        self.data_fetcher: DataFetcher | None = None
        self.choose_data_fetcher()
    
    def choose_data_fetcher(self):
        #django api
        if "REST_IMPLEMENTATION" in  os.environ:
            from .api.django.django_api import DjangoAPI
            self.data_fetcher = DjangoAPI()
            
    
