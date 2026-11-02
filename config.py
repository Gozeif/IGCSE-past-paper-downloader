"""Configurations For IGCSE Past Papers Downloader (dynamicpapers.com)"""
import os
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

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Subject pages are password protected. You can override this with the
# Set DYNAMICPAPERS_PASSWORD, or leave it unset to be prompted.
SITE_PASSWORD = os.environ.get("DYNAMICPAPERS_PASSWORD")

# --- Folders / files ----------------------------------------------------
DATA_FOLDER = "data"
MARK_SCHEME_FOLDER = "mark_scheme"
QUESTION_PAPERS_FOLDER = "question_papers"
MERGED_FOLDER = "MERGED"
MERGED_FILE = "merged.pdf"
MERGED_TEMP_FILE = "merged_temp.pdf"
DEBUG_HTML_FILE = "debug_page.html"

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
