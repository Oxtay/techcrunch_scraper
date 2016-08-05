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
import logging
import argparse
import numpy as np
import pandas as pd
import mechanize

from datetime import datetime, timedelta
from dateutil import relativedelta
from bs4 import BeautifulSoup as bs
from bs4 import SoupStrainer

TCRUNCH = 'https://techcrunch.com/'
DEFAULT_FILE = 'company_info.csv'

class TechCrunchScraper(object):
    """
    Scraping TechCrunch to retrieve company addresses
    """
    def __init__(self, start_date=None, end_date=None):
        self.companies_df = pd.DataFrame(columns=['company name', 'company website', 'article title', 'article url'])  # Dataframe to hold company data
        self.start_date = start_date
        self.end_date = end_date
        self.pages_to_scrape = []  # list of pages to scrape
        self.article_links = []

    def process(self):
        """
        One function to call to process from start to finish.
        """
        self.get_address()
        self.get_article_links()

    def get_address(self):
        """
        Get the list of addresses for the dates requested
        """
        # If no start date is set, take the date a day prior to current date and download for the previous day
        if self.start_date is None:
            self.start_date = datetime.now() - relativedelta.relativedelta(days=1)
        else:
            try:
                self.start_date = datetime.strptime(self.start_date, '%Y-%m-%d')
            except ValueError:
                print 'Start date is not in correct format. Reverting to default date.'

        if self.end_date is None:
            self.end_date = datetime.now() - relativedelta.relativedelta(days=1)
        else:
            try:
                self.end_date = datetime.strptime(self.end_date, '%Y-%m-%d')
            except ValueError:
                print 'End date is not in correct format. Reverting to default date.'

        if self.start_date > self.end_date:
            print 'Start date should be an older date than end date'
            return

        delta = self.end_date - self.start_date
        date_list = [(self.start_date+timedelta(days=i)).strftime('%Y/%m/%d') for i in range(delta.days+1)]

        for date in date_list:
            self.pages_to_scrape.append(TCRUNCH+date)

    def get_article_links(self):
        """
        From each page, get links to articles in that page
        """
        if not self.pages_to_scrape:
            print 'pages list is empty!'
            return

        # For now, let's ignore multiple pages of articles per day

        # for page in self.pages_to_scrape:
        #
        #     br = mechanize.Browser()
        #     br.open(page)
        #     br.select_form(nr=0)
        #
        #     # Find out how many pages to read
        #     soup = bs(br.response().read(), 'html.parser')
        #     total_articles = int(soup.find('ol', attrs={'class': 'pagination'}))
        #     num_pages = int(np.ceil(total_articles / 30.0))  # 30 articles per page

        br = mechanize.Browser()
        for page_link in self.pages_to_scrape:

            print "Fetching links on page: %s" % page_link

            br.open(page_link)
            page_html = br.response().read()
            soup = bs(page_html, 'html.parser', parse_only=SoupStrainer('a'))
            for link in soup:
                if link.has_attr('href') and link.has_attr('data-omni-sm') and link['data-omni-sm'].startswith('gbl_river_headline'):
                    self.article_links.append(link['href'])
            br.close()

    def scrape_article_page(self):
        """
        For each article link, find the company info
        """
        for article_link in self.article_links:
            company_info = self.get_company_info(article_link)
            self.companies_df = self.companies_df.append(company_info, ignore_index=True)

    @staticmethod
    def get_company_info(link):
        """
        Extracts company info
        :param link: link to each article
        :return: list of company info
        """
        company_info = {}
        br = mechanize.Browser()

        print "Company info on article: %s" % link

        br.open(link)
        page_html = br.response().read()

        # soup = bs(page_html, 'html.parser', parse_only=SoupStrainer('li', {'class': 'data-card crunchbase-card active'}))
        soup = bs(page_html, 'html.parser')

        company_info['article title'] = soup.find('h1', {'class': 'alpha tweet-title'}).text
        company_info['article url'] = link

        company_name_container = soup.find('a', {'class': 'cb-card-title-link'})
        if company_name_container is not None:
            company_info['company name'] = company_name_container.text.lstrip().rstrip()

        company_website_element = safe_list_get(soup.find_all('strong', string='Website'), 0, None)
        if company_website_element is not None:
            try:
                company_info['company website'] = company_website_element.next_sibling.next_sibling.contents[1]['href']
            except IndexError:
                company_info['company website'] = company_website_element.next_sibling.next_sibling.contents[0]['href']
        else:
            company_info['company website'] = None

        br.close()

        return company_info

    def save_to_csv(self):
        """
        save the dataframe to CSV
        :return: CSV file
        """
        self.companies_df.to_csv(DEFAULT_FILE, encoding='utf-8')


def safe_list_get(l, idx, default):
    try:
        return l[idx]
    except IndexError:
        return default


def parse_arguments(parser):
    """
    Setting the input arguments and options for the main function
    """
    parser.add_argument("-startdate",
                        "--start-date",
                        dest="start_date",
                        default=None,
                        help="Specifies the beginning date for scraping.\n"
                             "For example, for July 30, 2015, enter 2015-07-30")

    parser.add_argument("-enddate",
                        "--end-date",
                        dest="end_date",
                        default=None,
                        help="Specifies the end date for scraping.")

    parser.add_argument("-dir",
                        "--directory",
                        dest="directory",
                        help="Specifies the destination folder, where the file will be saved.\n"
                             "It will create the folder if it doesn't exist.")

    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s\t%(message)s')

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
    if cruncher.pages_to_scrape is None:
        return
    cruncher.get_article_links()
    cruncher.scrape_article_page()
    cruncher.save_to_csv()

    return


if __name__ == '__main__':
    main()
