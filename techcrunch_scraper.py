"""
The goal is to

Simple command line app to go to techcrunch.com, read each article and determine
which company (if any) is the primary subject matter of the article.
The output of the program will be a csv file with the following:

company name, company website, article title, article url

In the case where the company name and/or website cannot be determined then use n/a in
place of the name or website. The completed project should be as modular as possible,
and appropriately unit tested. Code should be appropriately commented. Project should
be checked into a public git repo under your github account.

Once the initial project is checked in then create a new branch in git and alter the csv format to:

article title, article url, company name, company website
"""
import os
import sys
import logging
import argparse
import pandas as pd
import mechanize

from datetime import datetime, timedelta
from dateutil import relativedelta
from bs4 import BeautifulSoup as bsoup

TCRUNCH = 'https://techcrunch.com/'


class TechCrunchScraper(object):
    """
    Scraping TechCrunch to retrieve company addresses
    """
    def __init__(self, start_date=None, end_date=None):
        self.companies_df = pd.DataFrame(columns=['company name', 'company website', 'article title', 'article url'])  # Dataframe to hold company data
        self.start_date = start_date
        self.end_date = end_date
        self.pages_to_scrape = []  # list of pages to scrape

    def get_address(self):
        """
        Get the list of addresses for the dates requested
        """
        # If no start date is set, take the date a month prior to current date and download for the previous month
        if self.start_date is None:
            self.start_date = (datetime.now() - relativedelta.relativedelta(months=1))
        else:
            try:
                self.start_date = datetime.strptime(self.start_date, '%Y-%m-%d')
            except ValueError:
                print 'Start date is not in correct format. Reverting to default date.'

        if self.end_date is None:
            self.end_date = datetime.now()
        else:
            try:
                self.end_date = datetime.strptime(self.end_date, '%Y-%m-%d')
            except ValueError:
                print 'End date is not in correct format. Reverting to default date.'

        delta = self.end_date - self.start_date
        date_list = [(self.start_date+timedelta(days=i)).strftime('%Y/%m/%d') for i in range(delta.days+1)]

        for date in date_list:
            self.pages_to_scrape.append(TCRUNCH+date)

        print(self.pages_to_scrape)
        return

    def save_to_csv(self):
        """
        save the dataframe to CSV
        :return: CSV file
        """
        self.companies_df.to_csv()


def parse_arguments(parser):
    """
    Setting the input arguments and options for the main function
    """
    parser.add_argument("-startdate", "--start-date",
                        dest="start_date",
                        default=None,
                        help="Specifies the beginning date for raw data.\n"
                             "For example, for July 30, 2015, enter 2015-07-30")

    parser.add_argument("-enddate", "--end-date",
                        dest="end_date",
                        default=None,
                        help="Specifies the end date for raw data.")

    parser.add_argument("-dir", "--directory",
                        dest="directory",
                        help="Specifies the destination folder, where the file will be saved.\n"
                             "It will create the folder if it doesn't exist.")

    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s\t%(message)s')

    if len(sys.argv) == 1:
        parser.print_help()

    options = parser.parse_args()

    return options


def main():
    """
    Main function
    """
    # Set the options and read the input
    description = "Extract Company information from TechCrunch articles"
    parser = argparse.ArgumentParser(description=description)

    options = parse_arguments(parser)

    if options.directory is None:
        options.directory = os.path.dirname(os.path.realpath(__file__))
    if not os.path.exists(options.directory):
        os.mkdir(options.directory)

    cruncher = TechCrunchScraper(start_date=options.start_date,
                                 end_date=options.end_date)

    cruncher.get_address()


if __name__ == '__main__':
    main()
