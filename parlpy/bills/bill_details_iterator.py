# todo bill_details_iterator
#   function shall take a DataFrame generated by BillsOverview and yield the details for each bill in series
#   it shall call get_summary(path), get_votes(bill_name) for each item in the DataFrame
import parlpy.bills.bill_list_fetcher as blf
import parlpy.bills.summary_fetcher as sf
import parlpy.utils.dates as session_dates
import parlpy.bills.bill_votes_fetcher as bvf

import datetime
import json
from typing import List, Iterable, NamedTuple

import pandas as pd


# class with member variables to hold information on a single bill/act
class BillDetails():
    def __init__(self,
                 b: pd.DataFrame,
                 summary: str,
                 divisions_list: List[bvf.DivisionInformation],
    ):
        base_url = "https://bills.parliament.uk"

        self.title_stripped = b.bill_title_stripped
        self.title_postfix = b.postfix
        self.sessions = b.session
        self.url = base_url + b.bill_detail_path
        self.last_updated = b.last_updated
        self.summary = summary
        self.divisions_list = divisions_list


# get the earliest and latest dates that the bill may have had divisions, latest is None if the session is ongoing
def get_start_and_end_dates(b):
    earliest_session = b.session[0]
    latest_session = b.session[-1]

    earliest_start_date = datetime.date.fromisoformat(
        session_dates.parliamentary_session_start_dates[earliest_session])

    try:
        latest_end_date = datetime.date.fromisoformat(
            session_dates.parliamentary_session_end_dates[latest_session])
    except TypeError:
        latest_end_date = None

    return earliest_start_date, latest_end_date


# yield a BillDetails object
def get_bill_details(overview: blf.BillsOverview, debug=False) -> Iterable[BillDetails]:
    for b in overview.bills_overview_data.itertuples():
        if debug:
            print(b)

        # use the bill name and narrow results using the start and end dates to get a list of divisions results object
        title_stripped = b.bill_title_stripped
        earliest_start_date, latest_end_date = get_start_and_end_dates(b)
        divisions_data_list = bvf.get_divisions_information(title_stripped, earliest_start_date, latest_end_date)

        # get the details path and use it to get summary for the bill
        detail_path = b.bill_detail_path
        summary = sf.get_summary(detail_path)

        bill_details = BillDetails(b, summary, divisions_data_list)

        yield bill_details
