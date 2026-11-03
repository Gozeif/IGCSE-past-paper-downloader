"""Configurations For IGCSE Past Papers Downloader (dynamicpapers.com)"""
import os
import sys
from dotenv import load_dotenv

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}

# --- Site ---------------------------------------------------------------
SITE_URL = "https://dynamicpapers.com/"
POSTPASS_URL = "https://dynamicpapers.com/wp-login.php?action=postpass"
TIMEOUT = 60

# Menu links under these paths are treated as subjects, labelled by board
BOARD_PATHS = {
    "CIE": "/past-papers/cambridge-past-papers/",
    "AQA": "/past-papers/past-papers-aqa/",
    "Edexcel": "/past-papers/edexcel-past-papers/",
    "Edexcel (recent)": "/edexcel-recent-papers/",
}

# Edexcel's menu has no subject codes, so each code maps to the exact menu name(s)
# of that subject (compared in lower case) under Edexcel's O Level / IGCSE
# sections. A code whose subject has no page on the site just reports
# "Invalid Paper Code". Add your own lines as needed.
EDEXCEL_CODES = {
    "4AA1": ["arabic"],                              # Arabic (First Language)
    "4AC1": ["accounting"],
    "4BI1": ["biology"],
    "4BS1": ["business"],
    "4CH1": ["chemistry"],
    "4CP1": ["computer science"],
    "4EA1": ["english language a"],
    "4EB1": ["english language b"],
    "4EC1": ["economics"],
    "4ES0": ["english as a second language"],
    "4ES1": ["english as a second language"],
    "4ET1": ["english literature"],
    "4FR1": ["french"],
    "4GE1": ["geography"],
    "4HB1": ["human biology"],
    "4IT1": ["ict", "information communication technology (ict)"],
    "4MA1": ["maths"],                               # Mathematics A
    "4MB1": ["mathematics b"],
    "4PH1": ["physics"],
    "4PM0": ["further pure mathematics"],
    "4PM1": ["further pure mathematics"],
    "4SP1": ["spanish"],
}
# Folder of the script, or of the .exe when built with PyInstaller
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(BASE_DIR, ".env"))

# Subject pages are password protected. Set the DYNAMICPAPERS_PASSWORD
# environment variable or put the password in settings.txt; if neither is
# set you are asked for it when it is needed.
SITE_PASSWORD = os.environ.get("DYNAMICPAPERS_PASSWORD")

# --- Folders / files ----------------------------------------------------
DATA_FOLDER = os.path.join(BASE_DIR, "IGCSE downloads")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.txt")
MARK_SCHEME_FOLDER = "mark_scheme"
QUESTION_PAPERS_FOLDER = "question_papers"
MERGED_FOLDER = "MERGED"
MERGED_FILE = "merged.pdf"
MERGED_TEMP_FILE = "merged_temp.pdf"
REMOVE_BLANK_PAGES = True
DEBUG_HTML_FILE = os.path.join(BASE_DIR, "debug_page.html")

# --- Filtering ----------------------------------------------------------
# File-name types that are skipped (examiner reports, grade thresholds, ...)
BANNED_PAPER_TYPES = ["ir", "gt", "er", "pef"]
SEASONS = ["summer", "mid-year(march)", "winter"]

# --- Prompts ------------------------------------------------------------
PROMPT_FOR_CODE = ("Paper Code (e.g. 0580, 9709, 9280, 4MA1 - or a name like "
                   "'edexcel maths'): ")
PROMPT_FOR_FILTER = "Do you want to exclude certain paper code (yes or no): "
PROMPT_FOR_FILTER_IN_SEASON = "Do you want to filter any code in {} (yes or no): "
PROMPT_FOR_PAPER_CODE = "Which codes to filter (seperated by space): "
PROMPT_OPERATION = "Do You Want To Download Past Papers Or Merge Them(download or merge): "

SETTINGS_TEMPLATE = """\
# IGCSE Past Paper Downloader - settings
# Lines starting with # are comments. Save this file after editing it.

[settings]
# Password for dynamicpapers.com. Leave empty to be asked when it is needed.
password =

# Where papers are saved. A plain name is created next to the program.
downloads_folder = IGCSE downloads

# File types that are never downloaded (examiner reports, grade thresholds...)
# Separate with spaces. Leave empty to download everything.
skip_types = ir gt er pef

# Remove "BLANK PAGE" pages from downloaded and merged PDFs (yes or no)
remove_blank_pages = yes

# Seconds to wait for the site before giving up on a request
timeout = 60
"""