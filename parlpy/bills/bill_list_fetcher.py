from urllib.request import urlopen
import urllib.parse
from collections import OrderedDict
import re
import time
import datetime
import pickle

import pandas as pd
import numpy

from bs4 import BeautifulSoup


# class that will have a method to fetch all bill titles, with its associated data:
# * associated link to further details
# * last updated date
# and will update the list by fetching each https://bills.parliament.uk page in series until the oldest updated date
# is older than the bills_df_last_updated, amending the bills_df as it does so (planned)
class BillsOverview():
    def __init__(self, debug=False):
        # whether to print output as it is collected
        self.debug = debug

        self.bills_overview_data = pd.DataFrame([], columns=["bill_title", "last_updated", "bill_detail_path"])
        self.last_updated = None

        # record number of pages
        self.pages_updated_this_update = 0

        self.listed_bills_counter = 0 # debugging var

        self.__bills_overview_scheme = "https"
        self.__bills_overview_netloc = "bills.parliament.uk"

        self.__bills_overview_session = {
            "All": "0",
            "2019-21": "35",
            "2019-19": "34", # a jump here for unknown reason
            "2017-19": "30",
            "2016-17": "29",
            "2015-16": "28",
            "2014-15": "27",
            "2013-14": "26",
            "2012-13": "25",
            "2010-12": "24",
            "2009-10": "23",
            "2008-09": "22",
            "2007-08": "21",
            "2006-07": "20",
            "2005-06": "19",
            "2004-05": "18"
        }
        self.__bills_overview_sort_order = {
            "Title (A-Z)": "0",
            "Updated (newest first)": "1",
            "Updated (oldest first)": "2",
            "Title (Z-A)": "3"
        }

    # get the total number of pages of bills for the selected session
    # there are many other possible methods of doing this - uncertain which is most robust
    def __determine_number_pages_for_session(self, session):
        page_query_string = urllib.parse.urlencode(
            OrderedDict(
                Session=session
            )
        )

        url = urllib.parse.urlunparse((
            self.__bills_overview_scheme, self.__bills_overview_netloc, "", "", page_query_string, ""
        ))

        html_data = urlopen(url)
        data_bs = BeautifulSoup(html_data.read(), 'html.parser')
        page_selection_elements = data_bs.find_all("a", href=re.compile("page=*"))

        max_page = 1 # there is always at least one page for a valid session
        for pt in page_selection_elements:
            page = int(pt["href"].split('page=')[1])

            if page > max_page:
                max_page = page

        if self.debug:
            print("max page = {}".format(max_page))

        return max_page

    def __get_title_list_from_card_tags(self, card_tags):
        titles = []
        for o in card_tags:
            title = o.find(class_="primary-info")
            titles.append(title.text)

        if self.debug:
            print("title list for page {}".format(titles))

        return titles

    def __get_updated_dates_list_from_card_tags(self, card_tags):
        updated_dates = []
        for o in card_tags:
            updated_date = o.find(class_="indicators-left")
            updated_date = updated_date.text.split("updated: ")[1]
            updated_date = updated_date.splitlines()[0]
            updated_date = updated_date.rsplit(" ", 1)[0]

            updated_date_datetime = datetime.datetime.strptime(updated_date, '%d %B %Y at %H:%M')

            updated_dates.append(updated_date_datetime)

        return updated_dates

    def __get_bill_data_path_list_from_card_tags(self, card_tags):
        bill_details_paths = []
        for o in card_tags:
            bill_detail_path_tag = o.find(class_="overlay-link")
            bill_data_path = bill_detail_path_tag["href"]

            bill_details_paths.append(bill_data_path)

        return bill_details_paths

    def put_bill_info_in_list_into_bills_overview_data(self, bill_tuple_list):
        if len(bill_tuple_list) > 0:
            bill_tuple_arr = numpy.array(bill_tuple_list)

            page_df = pd.DataFrame(bill_tuple_arr, columns=["bill_title", "last_updated", "bill_detail_path"])

            new_indices = [x for x in
                           range(len(self.bills_overview_data.index), len(self.bills_overview_data.index) + len(page_df))]
            page_df.index = new_indices

            self.bills_overview_data = pd.concat([self.bills_overview_data, page_df])

            print("last item on page: {}".format(page_df.iloc[-1]))

    # puts the partial dataframe containing titles, their last updated dates and bill details paths into dataframe
    # member variable
    # if check_last_updated, only add up to the point that the bill's updated date is newer than our scraper last
    # updated
    def __add_page_data_to_bills_overview_data(
            self,
            titles,
            updated_dates,
            bill_details_paths,
            check_last_updated=True):
        bill_tuple_list = []

        try:
            with open("test.p", "rb") as f:
                loaded_last_updated = pickle.load(f)
        except (FileNotFoundError) as e:
            # this is the case if the pickle file has been manually deleted, or if this is the first time
            # get_changed_bills_in_session is running
            loaded_last_updated = None

        for i in range(len(titles)):
            if loaded_last_updated != None and check_last_updated:
                delta_from_last_update_call = loaded_last_updated - updated_dates[i]
                if self.debug:
                    print("bill title: {}".format(titles[i]))
                    print("bill updated date: {} type {}".format(updated_dates[i], type(updated_dates[i])))
                    print("last updated: {}".format(loaded_last_updated))
                if delta_from_last_update_call.total_seconds() > 0:
                    if self.debug:
                        print("found newest bill NOT updated recently (first to be discarded)")
                        print("delta in seconds {}".format(delta_from_last_update_call.total_seconds()))
                        print(titles[i])
                        print(updated_dates[i])

                    self.put_bill_info_in_list_into_bills_overview_data(bill_tuple_list)

                    got_all_updated_bills = True
                    return got_all_updated_bills

                else:
                    print("found bill updated recently {}".format(titles[i]))

            bill_tuple_list.append((titles[i], updated_dates[i], bill_details_paths[i]))

            self.listed_bills_counter += 1

        self.put_bill_info_in_list_into_bills_overview_data(bill_tuple_list)

        # last item was updated since we last called, so proceed to next page
        return False

    # adds bill overview information to self.bills_overview_data
    def __fetch_all_overview_info_on_page(self, session, sort_order, page):
        page_query_string = urllib.parse.urlencode(
            OrderedDict(
                Session=session,
                BillSortOrder=sort_order,
                page=str(page),
            )
        )

        url = urllib.parse.urlunparse((
            self.__bills_overview_scheme, self.__bills_overview_netloc, "", "", page_query_string, ""
        ))

        html_data = urlopen(url)
        data_bs = BeautifulSoup(html_data.read(), 'html.parser')

        card_tags = data_bs.find_all(class_="card-clickable")

        titles = self.__get_title_list_from_card_tags(card_tags)
        updated_dates = self.__get_updated_dates_list_from_card_tags(card_tags)
        bill_data_paths = self.__get_bill_data_path_list_from_card_tags(card_tags)

        return (titles, updated_dates, bill_data_paths)

    def __update_bills_overview_up_to_page(self, session_code, max_page, fetch_delay, smart_update=True):
        # get in order of updated, because update_bills_overview_up_to_page is planned to only crawl pages with
        # bills updated since the method was last called
        sort_order_code = self.__bills_overview_sort_order["Updated (newest first)"]

        for i in range(1, max_page+1):
            time.sleep(fetch_delay)

            (titles, updated_dates, bill_data_paths) = self.__fetch_all_overview_info_on_page(session_code, sort_order_code, i)

            self.__add_page_data_to_bills_overview_data(titles, updated_dates, bill_data_paths, check_last_updated=False)

        self.last_updated = datetime.datetime.now()
        print(self.last_updated)

    # method to update self.bills_overview_data dataframe with overview information about bills from given session, or
    # all sessions
    # currently gets titles, updated dates, further information paths
    # fetch_delay is approx time in seconds of delay between fetching site pages
    def update_all_bills_in_session(
            self,
            session_name="2019-21",
            fetch_delay=0,
            update_last_updated=False
    ):
        # reset df
        self.bills_overview_data = pd.DataFrame([], columns=["bill_title", "last_updated", "bill_detail_path"])

        # get the integer string corresponding to session string
        session_code = self.__bills_overview_session[session_name]

        max_page = self.__determine_number_pages_for_session(session_code)

        self.__update_bills_overview_up_to_page(session_code, max_page, fetch_delay)

    def __update_bills_overview_with_updated_bills_only_up_to_page(self, session_code, max_page, fetch_delay):
        sort_order_code = self.__bills_overview_sort_order["Updated (newest first)"]

        for i in range(1, max_page + 1):
            time.sleep(fetch_delay)
            (titles, updated_dates, bill_data_paths) = self.__fetch_all_overview_info_on_page(session_code,
                                                                                              sort_order_code, i)

            got_all_updated_bills = self.__add_page_data_to_bills_overview_data(
                titles, updated_dates, bill_data_paths, check_last_updated=True)
            # if we have all the bills which were updated since we last checked, no need to check any more pages
            if got_all_updated_bills:
                break

        # todo - for tests, set this value to be eg a week ago and see which bills are collected
        last_updated_to_be_pickled = datetime.datetime.now()
        print("saving last_updated_to_be_pickled {}".format(last_updated_to_be_pickled))
        with open("test.p", "wb") as f:
            pickle.dump(last_updated_to_be_pickled, f)
        print(self.last_updated)

    # this method uses a pickled variable (so that ths package can be run periodically)
    # puts into self.bills_overview_data, bills which have been updated since the method was last called
    # these can then be compared to values in a database for example
    def get_changed_bills_in_session(self, session_name="2019-21", fetch_delay=0):
        # reset df ready for new data
        self.bills_overview_data = pd.DataFrame([], columns=["bill_title", "last_updated", "bill_detail_path"])

        session_code = self.__bills_overview_session[session_name]

        max_page = self.__determine_number_pages_for_session(session_code)

        self.__update_bills_overview_with_updated_bills_only_up_to_page(session_code, max_page, fetch_delay)
