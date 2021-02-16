import pandas as pd
import datetime
import numpy as np

import parlpy.bills.bill_list_fetcher

import unittest



class TestOverview(unittest.TestCase):
    # create BillsOverview object ready for tests
    # also print result
    def setUp(self):
        test_fetcher = parlpy.bills.bill_list_fetcher.BillsOverview()
        test_fetcher.update_all_bills_in_session()

        self.test_fetcher = test_fetcher

        pd.set_option("display.max_columns", len(self.test_fetcher.bills_overview_data.columns))

        print(self.test_fetcher.bills_overview_data)

        print(self.test_fetcher.bills_overview_data[
                  self.test_fetcher.bills_overview_data.bill_title == "Fire Safety Bill"
                  ])

    # test types of dataframe
    def test_dataframe_types(self):
        #self.assertIsInstance(self.test_fetcher.bills_overview_data, pd.DataFrame)
        print(self.test_fetcher.bills_overview_data.dtypes)
        # strings are stored as objects in dataframes
        self.assertTrue(self.test_fetcher.bills_overview_data.bill_title.dtype == object)

        print("dtype value")
        print(self.test_fetcher.bills_overview_data.last_updated.dtype)

        self.assertTrue(self.test_fetcher.bills_overview_data.last_updated.dtype == np.dtype('datetime64[ns]'))
        self.assertTrue(self.test_fetcher.bills_overview_data.bill_detail_path.dtype == object)

if __name__ == '__main__':
    unittest.main()