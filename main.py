"""IGCSE Past Papers Downloader (source: dynamicpapers.com)

Works for CIE, AQA and Edexcel subjects: type a paper code (0580, 9709, 9280,
4MA1, ...) or part of a subject name (for example "edexcel maths").
"""
import os
import re
from urllib.parse import unquote, urljoin, urlparse

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

# --------------------------------------------------------------------------
# Reading papers off a subject page
# --------------------------------------------------------------------------
def _year_from_yy(yy):
    yy = int(yy)
    return 2000 + yy if yy < 70 else 1900 + yy


def _paper(stem, url, year, season, paper_type, variant):
    return {
        "name": stem,
        "url": url,
        "year": year,
        "season": season,
        "type": paper_type,
        "variant": variant,
        "folder": (config.MARK_SCHEME_FOLDER if paper_type == "ms"
                   else config.QUESTION_PAPERS_FOLDER),
    }


def _context_year(link):
    """Year from the closest heading above a link (for pages that group
    papers under year headings)"""
    heading = link.find_previous(
        lambda tag: tag.name in HEADING_TAGS and YEAR_RE.search(
            tag.get_text()))
    if heading is None:
        return None
    year_match = YEAR_RE.search(heading.get_text())
    return int(year_match.group()) if year_match else None


def parse_paper(url, text, link=None):
    """Works out year/season/type of a pdf link, or None if there is no year.
    Understands CIE and Edexcel file names, else guesses from name and text."""
    stem = os.path.splitext(os.path.basename(unquote(urlparse(url).path)))[0]

    match = CIE_RE.fullmatch(stem)
    if match:
        return _paper(stem, url, _year_from_yy(match["yy"]),
                      match["season"].lower(), match["type"].lower(),
                      match["variant"] or "")

    match = EDEXCEL_RE.match(stem)
    if match:
        year, month = int(match["date"][:4]), int(match["date"][4:6])
        if 1990 <= year <= 2100 and 1 <= month <= 12:
            kind = match["type"].lower()
            return _paper(stem, url, year, NUMBER_SEASON[month],
                          EDEXCEL_TYPES.get(kind, kind), match["paper"])

    # Unknown naming (e.g. AQA): guess from the file name and the link text
    haystack = "{} {}".format(stem, text).lower()
    month = re.search(MONTH_RE, haystack)

    year = None
    found = YEAR_RE.search(haystack)
    if found:
        year = int(found.group())
    elif month:
        short = re.search(MONTH_RE + r"[\s_-]?(\d{2})(?!\d)", haystack)
        if short:
            year = _year_from_yy(short.group(2))
    if year is None and link is not None:
        year = _context_year(link)
    if year is None:
        return None

    season = MONTH_SEASON[month.group(1)[:3]] if month else "x"

    paper_type = "ms" if re.search(
        r"(?<![a-z])(ms|rms|msc|mark ?scheme|markscheme|marking)(?![a-z])",
        haystack) else "qp"
    for banned in config.BANNED_PAPER_TYPES:
        if re.search(r"(?<![a-z])" + banned + r"(?![a-z])", haystack):
            paper_type = banned
            break

    return _paper(stem, url, year, season, paper_type, "")


def collect_papers(soup, base_url, start_year, end_year):
    """Returns {name: paper} for every pdf linked on a page whose year is in
    range"""
    found, unknown = {}, []
    for link in soup.find_all("a", href=True):
        url = urljoin(base_url, link["href"])
        if not urlparse(url).path.lower().endswith(".pdf"):
            continue

        paper = parse_paper(url, link.get_text(" ", strip=True), link)
        if paper is None:
            unknown.append(url)
        elif start_year <= paper["year"] <= end_year:
            found[paper["name"]] = paper

    if unknown:
        print("  note: {} pdf link(s) had no recognizable year, e.g. {}".format(
            len(unknown), unknown[0]))
    return found


def get_papers(subject_url, start_year, end_year):
    """Returns all papers of a subject between start and end year"""
    soup = get_page(subject_url)
    papers = collect_papers(soup, subject_url, start_year, end_year)

    if not papers:
        # Maybe the subject page only links to per-year pages: follow those
        seen = {subject_url}
        for link in soup.find_all("a", href=True):
            href = link.get("href")
            if not isinstance(href, str):
                continue
            url = urljoin(subject_url, href)
            if url in seen or not url.startswith(subject_url):
                continue
            seen.add(url)

            year = YEAR_RE.search(link.get_text()) or YEAR_RE.search(url)
            if year and not start_year <= int(year.group()) <= end_year:
                continue
            papers.update(collect_papers(get_page(url), url,
                                         start_year, end_year))

    if not papers:
        with open(config.DEBUG_HTML_FILE, "w", encoding="utf-8") as file:
            file.write(str(soup))
        raise Exception(
            "No papers found in {}. The page layout may differ from what the "
            "script expects - see {}".format(subject_url,
                                             config.DEBUG_HTML_FILE))

    return papers


# --------------------------------------------------------------------------
# Download
# --------------------------------------------------------------------------
def filter_papers(papers, to_filter):
    """Drops banned paper types and the variant codes the user excluded"""
    output = {}

    for name, paper in papers.items():
        if paper["type"] in config.BANNED_PAPER_TYPES:
            continue
        excluded = [c.lower() for c in to_filter.get(paper["season"], [])]
        if paper["variant"].lower() in excluded:
            continue
        output[name] = paper

    return output


def download_papers(paper_code, papers):
    """Downloads all papers (a dict of paper dicts)"""
    base = os.path.join(config.DATA_FOLDER, folder_name(paper_code))
    mkdir(os.path.join(base, config.QUESTION_PAPERS_FOLDER))
    mkdir(os.path.join(base, config.MARK_SCHEME_FOLDER))

    # Oldest first. Season letters sort chronologically (j < m < s < r < w).
    ordered = sorted(papers.values(),
                     key=lambda p: (p["year"], p["season"], p["name"]))

    for paper in ordered:
        safe_name = re.sub(r'[<>:"/\\|?*\s]+', "_", paper["name"])
        name = os.path.join(base, paper["folder"],
                            "{}_{}.pdf".format(paper["year"], safe_name))

        if os.path.exists(name):
            print("Skipping {} (already downloaded)".format(paper["name"]))
            continue

        print("Downloading {}".format(paper["name"]))
        response = fetch(paper["url"])
        if response.status_code != 200 or not response.content.startswith(b"%PDF"):
            print("  failed (HTTP {}), skipping".format(response.status_code))
            continue

        with open(name + "_temp", "wb") as file:
            file.write(response.content)

        try:
            remove_blank_pages(name + "_temp", name)
            os.remove(name + "_temp")
        except Exception as error:  # pylint: disable=broad-except
            # keep the original file rather than losing the download
            print("  could not strip blank pages ({}), keeping as is".format(
                error))
            os.replace(name + "_temp", name)


def download():
    """Downloads past papers"""
    paper_code, start_year, end_year, to_filter = get_data_from_user()
    subject_urls = get_subject_urls(paper_code)

    papers, errors = {}, []
    for subject_url in subject_urls:
        try:
            papers.update(get_papers(subject_url, start_year, end_year))
        except Exception as error:  # pylint: disable=broad-except
            print("  {}".format(error))
            errors.append(error)

    if not papers:
        raise errors[0] if errors else Exception("No papers found")

    papers = filter_papers(papers, to_filter)
    print("Found {} files".format(len(papers)))
    download_papers(paper_code, papers)


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
