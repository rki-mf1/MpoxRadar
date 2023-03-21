import unittest
import os
from datetime import date

from data import load_all_sql_files
from pages.utils_worldMap_explorer import DateSlider

DB_DUMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sql_dumps")


def to_date(d):
    return date.fromisoformat(d)


class TestDateSlider(unittest.TestCase):
    def setUp(self):
        self.db_name = "mpx_test_04"
        self.processed_df_dict = load_all_sql_files(self.db_name, caching=False)
        self.date_slider = DateSlider(self.processed_df_dict)

    def test_dates(self):
        assert (self.date_slider.min_date == date(2022, 6, 28))
        assert (self.date_slider.max_date == date(2022, 10, 1))
        assert len(self.date_slider.date_list) == 96

    def test_unix_time_millis(self):
        assert 1670022000 == DateSlider.unix_time_millis(date(2022, 12, 3))

    def test_unix_to_date(self):
        assert DateSlider.unix_to_date(1669935600) == date(2022, 12, 2)
        assert DateSlider.unix_to_date(1672527600) == date(2023, 1, 1)

    def test_get_all_dates_in_interval(self):
        dates = [1669935600, 1672527600]
        interval = 9
        date_list = self.date_slider.get_all_dates_in_interval(dates, interval)
        correct_dates = [date(2022, 12, 24), date(2022, 12, 25), date(2022, 12, 26),
                         date(2022, 12, 27), date(2022, 12, 28), date(2022, 12, 29),
                         date(2022, 12, 30), date(2022, 12, 31), date(2023, 1, 1)]
        self.assertListEqual(date_list, correct_dates)


