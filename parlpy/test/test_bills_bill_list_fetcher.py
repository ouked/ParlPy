import pandas as pd
import datetime
import numpy as np

from parlpy.bills.bill_list_fetcher import BillsOverview

import unittest


class TestOverview(unittest.TestCase):
    # create BillsOverview object ready for tests
    # also print result
    def setUp(self):
        test_fetcher = BillsOverview(debug=True)
        test_fetcher.update_all_bills_in_session()

        self.test_fetcher = test_fetcher

        pd.set_option("display.max_columns", len(self.test_fetcher.bills_overview_data.columns))

        print(self.test_fetcher.bills_overview_data)

        print(self.test_fetcher.bills_overview_data[
                  self.test_fetcher.bills_overview_data.bill_title == "Fire Safety Bill"
                  ])

    # test types of dataframe
    def test_dataframe_types(self):
        self.assertIsInstance(self.test_fetcher.bills_overview_data, pd.DataFrame)

        print(self.test_fetcher.bills_overview_data.dtypes)

        # strings are stored as objects in dataframes
        self.assertTrue(self.test_fetcher.bills_overview_data.bill_title.dtype == object)
        self.assertTrue(self.test_fetcher.bills_overview_data.bill_detail_path.dtype == object)

        # check that last_updated is stored as datetime64[ns]
        self.assertTrue(self.test_fetcher.bills_overview_data.last_updated.dtype == np.dtype('datetime64[ns]'))

    # todo: check there are no duplicates in dataframe
    def test_no_duplicates(self):
        pass

    # test dataframe update procedure:
    # * times (first scrape should be older than second scrape)
    # * todo: number of bills updated (first scrape should have more bills updated than second scrape)
    # * number of pages visited during scrape (first should visit more pages than second)
    def test_update_procedure(self):
        first_update_time = self.test_fetcher.last_updated
        first_pages_updated = self.test_fetcher.pages_updated_this_update

        self.test_fetcher.update_all_bills_in_session()
        second_update_time = self.test_fetcher.last_updated
        second_pages_updated = self.test_fetcher.pages_updated_this_update

        delta = second_update_time - first_update_time
        self.assertTrue(delta.total_seconds() > 0)

        self.assertTrue(first_pages_updated > second_pages_updated)


if __name__ == '__main__':
    unittest.main()