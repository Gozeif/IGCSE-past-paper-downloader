"""IGCSE Past Papers Downloader"""
import os
import re

import requests
import bs4
from pypdf import PdfReader, PdfWriter
import config

SESSION = requests.Session()
SESSION.headers.update(config.HEADERS)

# CIE:     0580_s19_qp_12.pdf        Edexcel: 4MA1_1H_que_20190515.pdf
CIE_RE = re.compile(
    r"(?P<code>\d{4})_(?P<season>[smwy])(?P<yy>\d{2})_(?P<type>[a-z]{2})"
    r"(?:_(?P<variant>[\w-]+))?", re.IGNORECASE)
EDEXCEL_RE = re.compile(
    r"(?P<code>[A-Z0-9]{4,5})_(?P<paper>[0-9A-Z]+)_(?P<type>[a-z]+)_"
    r"(?P<date>\d{8})", re.IGNORECASE)
EDEXCEL_TYPES = {"que": "qp", "rms": "ms", "msc": "ms"}

YEAR_RE = re.compile(r"(?<!\d)(?:19|20)\d{2}(?!\d)")
MONTH_RE = (r"(?<![a-z])(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|"
            r"june?|july?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|"
            r"nov(?:ember)?|dec(?:ember)?)(?![a-z])")
MONTH_SEASON = {"jan": "j", "feb": "j", "mar": "m", "apr": "m", "may": "s",
                "jun": "s", "jul": "s", "aug": "r", "sep": "w", "oct": "w",
                "nov": "w", "dec": "w"}
NUMBER_SEASON = {1: "j", 2: "j", 3: "m", 4: "m", 5: "s", 6: "s", 7: "s",
                 8: "r", 9: "w", 10: "w", 11: "w", 12: "w"}
HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6", "strong", "b", "summary"}


def mkdir(name):
    """Makes a dir (and parents) if that dir does not exist"""
    os.makedirs(name, exist_ok=True)


def folder_name(paper_code):
    """Turns what the user typed into a safe folder name"""
    return re.sub(r"[^\w.-]+", "_", paper_code.strip()).strip("_") or "papers"
def get_paper_data(paper_name):
    """Gets paper code and paper type based on paper name"""
    split = paper_name.split("_")
    code = split[-1]
    paper_type = split[-2]

    if len(split) == 5:
        code = split[-2] + split[-3]
        paper_type = split[-1]

    elif len(split) == 3:
        code = "00"
        paper_type = split[-1]

    return code, paper_type

def pdf_merge(folder):
    """Merges all pdfs in a folder (in name order) and returns the writer"""
    pdfs = sorted(f for f in os.listdir(folder)
                  if os.path.isfile(os.path.join(folder, f)))

    merger = PdfWriter()

    for pdf in pdfs:
        merger.append(os.path.join(folder, pdf))

    return merger


def is_blank_page(page):
    """True if the page says BLANK PAGE. If the text can't be read, the page
    is kept (some PDFs have malformed fonts that crash text extraction)."""
    try:
        return "BLANK PAGE" in (page.extract_text() or "")
    except Exception:  # pylint: disable=broad-except
        return False


def remove_blank_pages(input_file_name, output_file_name):
    """Removes all blank pages from a pdf"""
    with open(input_file_name, "rb") as input_file:
        reader = PdfReader(input_file)
        writer = PdfWriter()

        for page in reader.pages:
            if not is_blank_page(page):
                writer.add_page(page)

        with open(output_file_name, "wb") as output_file:
            writer.write(output_file)


def get_data_from_user():
    """Ask And Get Data About Subject And Dates From User"""
    to_filter = {
        "s": [],
        "m": [],
        "w": [],
    }
    paper_code = input(config.PROMPT_FOR_CODE).strip()
    start_year = int(input("Start Year: "))
    end_year = int(input("End Year: "))

    should_filter = input(config.PROMPT_FOR_FILTER).strip().lower() == "yes"
    if should_filter:
        for season in config.SEASONS:
            answer = input(config.PROMPT_FOR_FILTER_IN_SEASON.format(season))
            if answer.strip().lower() == "yes":
                codes_to_filter = input(config.PROMPT_FOR_PAPER_CODE)
                to_filter[season[0]].extend(codes_to_filter.split())

    return paper_code, start_year, end_year, to_filter

def get_subject_url(paper_code):
    """Gets Subject's URL Based On Subject Code"""
    html_data = requests.get(config.BASE_URL, headers=config.HEADERS).content
    soup = bs4.BeautifulSoup(html_data, 'lxml')
    div = soup.find("div", attrs={"class":"entry clr", "itemprop" : "text"})
    subjects = div.findAll("p")

    for subject in subjects:
        if paper_code in subject.getText():
            return subject.find("a").get("href")

    raise Exception("Invalid Paper Code")

def get_each_years_url(subject_url, start_year, end_year):
    """Returns each years url from start year to end year of a subject"""
    output = []
    html_data = requests.get(subject_url, headers=config.HEADERS).content
    soup = bs4.BeautifulSoup(html_data, 'lxml')
    div = soup.find("div", attrs={"class":"entry clr", "itemprop" : "text"})
    years_to_get = list(range(start_year, end_year + 1))
    years = div.findAll("p")

    for year in years:
        try:
            link = year.find("a").get("href")
            if any([str(year_to_get) in link and "past-papers" in link
                    for year_to_get in years_to_get]):
                output.append(link)
        except AttributeError:
            pass

# --------------------------------------------------------------------------
# Site access
# --------------------------------------------------------------------------
def fetch(url):
    """GET through the shared session (keeps the password cookie)"""
    return SESSION.get(url, timeout=config.TIMEOUT)


def _soup(html):
    return bs4.BeautifulSoup(html, "lxml")


def _is_locked(soup):
    """True if the page is showing WordPress' password form"""
    return soup.find("input", attrs={"name": "post_password"}) is not None


def get_password():
    """Site password from the environment, or asked for once"""
    if not config.SITE_PASSWORD:
        config.SITE_PASSWORD = input("Site password: ").strip()
    return config.SITE_PASSWORD


def get_page(url):
    """Fetches a page, entering the site password if the page is protected"""
    soup = _soup(fetch(url).content)
    if not _is_locked(soup):
        return soup

    # WordPress password form: POST it with the page as Referer; the response
    # sets a cookie on the session which unlocks pages with that password.
    SESSION.post(
        config.POSTPASS_URL,
        data={"post_password": get_password(), "Submit": "Enter"},
        headers={"Referer": url},
        timeout=config.TIMEOUT,
    )
    soup = _soup(fetch(url).content)
    if _is_locked(soup):
        raise Exception("{} is still locked - is the password correct for "
                        "this page?".format(url))
    return soup



def get_papers_urls(year_url):
    """return all papers' url from a year url"""
    papers_urls = {}
    html_data = requests.get(year_url, headers=config.HEADERS).content
    soup = bs4.BeautifulSoup(html_data, 'lxml')
    div = soup.find("div", attrs={"class":"entry-content clr", "itemprop" : "text"})
    papers = div.findAll("p")

    for paper in papers:
        if " " not in paper.getText():
            papers_urls[paper.getText()] = paper.find("a").get("href")

    return papers_urls

def download_papers(paper_code, years_urls, to_filter):
    """Download all papers from a dict of paper urls"""
    for year_url in years_urls:
        papers_urls = get_papers_urls(year_url)
        papers_urls = filter_papers(papers_urls, to_filter)

        question_papers_folder = "{}/{}/{}".format(
            config.DATA_FOLDER,
            paper_code,
            config.QUESTION_PAPERS_FOLDER
        )

        mkdir(question_papers_folder)
        mkdir("{}/{}/{}".format(config.DATA_FOLDER, paper_code, config.MARK_SCHEME_FOLDER))
        num = len(os.listdir(question_papers_folder))

        for paper_name, paper_url in papers_urls.items():
            _, paper_type = get_paper_data(paper_name)
            print("Downloading {}".format(paper_name))

            if paper_type != "ms":
                folder = config.QUESTION_PAPERS_FOLDER
            else:
                folder = config.MARK_SCHEME_FOLDER

            data = requests.get(paper_url, headers=config.HEADERS).content

            name = "{}/{}/{}/{}_{}.pdf".format(config.DATA_FOLDER,
                                               paper_code,
                                               folder,
                                               num,
                                               paper_name)
            with open(name+"_temp", "wb") as file:
                file.write(data)

            remove_blank_pages(name+"_temp", name)
            os.remove(name+"_temp")


def filter_papers(papers_urls, to_filter):
    """Filters papers"""
    output = {}

    for paper_name, paper_url in papers_urls.items():
        season = paper_name.split("_")[1][0]
        code, paper_type = get_paper_data(paper_name)

        if code not in to_filter[season] and paper_type not in config.BANNED_PAPER_TYPES:
            output[paper_name] = paper_url

    return output


def download():
    """Downloads past papers"""
    paper_code, start_year, end_year, to_filter = get_data_from_user()
    subject_url = get_subject_url(paper_code)
    years_urls = get_each_years_url(subject_url, start_year, end_year)

    mkdir(config.DATA_FOLDER)
    mkdir(paper_code)

    download_papers(paper_code, years_urls, to_filter)

def merge():
    """merges past papers"""
    paper_code = input("Enter Paper Code To Merge: ")
    os.chdir(config.DATA_FOLDER)

    os.chdir(folder_name(paper_code))
    mkdir(config.MERGED_FOLDER)

    merger = pdf_merge(config.QUESTION_PAPERS_FOLDER)

    os.chdir(config.MERGED_FOLDER)
    with open(config.MERGED_TEMP_FILE, "wb") as file:
        merger.write(file)

    remove_blank_pages(config.MERGED_TEMP_FILE, config.MERGED_FILE)
    os.remove(config.MERGED_TEMP_FILE)


def main():
    """Main Loop"""
    operation = input(config.PROMPT_OPERATION)
    if operation.lower() == "merge":
        merge()
    else:
        download()


if __name__ == "__main__":
    main()
