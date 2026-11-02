"""IGCSE Past Papers Downloader"""
import os
import re
from urllib.parse import urljoin, urlparse

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


# --------------------------------------------------------------------------
# Finding the subject (any board)
# --------------------------------------------------------------------------
def parse_subjects(soup):
    """Reads every subject link out of the site menu"""
    subjects = {}
    for link in soup.find_all("a", href=True):
        url = urljoin(config.SITE_URL, link["href"])
        path = urlparse(url).path.rstrip("/")
        board = next((name for name, prefix in config.BOARD_PATHS.items()
                      if prefix in url and path != prefix.rstrip("/")), None)
        if board is None:
            continue

        item = link.find_parent("li")
        if item is not None and item.find("ul") is not None:
            continue  # a menu category (has sub-items), not a subject

        parts = []
        for parent in reversed(link.find_parents("li")):
            anchor = parent.find("a")
            if anchor is not None:
                parts.append(anchor.get_text(" ", strip=True))

        subjects[url] = {
            "board": board,
            "name": link.get_text(" ", strip=True),
            "label": " > ".join(parts),
            "url": url,
        }
    return list(subjects.values())


def find_subjects(query, subjects):
    """Subjects whose title contains the code; else (Edexcel codes) subjects
    with the mapped menu name; else subjects whose menu path has all words"""
    query = query.strip()
    if not query:
        return []

    pattern = re.compile(
        r"(?<![A-Za-z0-9])" + re.escape(query) + r"(?![A-Za-z0-9])",
        re.IGNORECASE)
    matches = [s for s in subjects if pattern.search(s["name"])]
    if matches:
        return matches

    names = config.EDEXCEL_CODES.get(query.upper())
    if names:
        return [s for s in subjects
                if s["board"].startswith("Edexcel")
                and "o level" in s["label"].lower()
                and s["name"].lower() in names]

    words = query.lower().split()
    return [s for s in subjects
            if all(word in s["label"].lower() for word in words)]


def choose_subjects(matches):
    """Lets the user pick when several subjects match"""
    if len(matches) == 1:
        print("Using: {} ({})".format(matches[0]["label"], matches[0]["url"]))
        return matches
    if len(matches) > 40:
        raise Exception("{} subjects match - be more specific "
                        "(a code or a longer name)".format(len(matches)))

    print("Several subjects match:")
    for number, subject in enumerate(matches, 1):
        print("  [{}] {}".format(number, subject["label"]))
    answer = input("Pick number(s) separated by commas, or 'all': ")
    if answer.strip().lower() == "all":
        return matches

    chosen = []
    for part in answer.split(","):
        part = part.strip()
        if part.isdigit() and 1 <= int(part) <= len(matches):
            chosen.append(matches[int(part) - 1])
    if not chosen:
        raise Exception("No valid selection")
    return chosen


def get_subject_urls(paper_code):
    """Finds the page(s) of a subject from a code or name"""
    soup = _soup(fetch(config.SITE_URL).content)
    matches = find_subjects(paper_code, parse_subjects(soup))
    if not matches:
        raise Exception("Invalid Paper Code")
    return [subject["url"] for subject in choose_subjects(matches)]

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
