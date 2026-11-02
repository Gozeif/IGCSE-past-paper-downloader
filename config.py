"""Configurations For IGCSE Past Papers Downloader"""
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


load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Subject pages are password protected. You can override this with the
# DYNAMICPAPERS_PASSWORD environment variable instead of keeping it in code.
SITE_PASSWORD = os.environ.get("DYNAMICPAPERS_PASSWORD")

# --- Folders / files ----------------------------------------------------
DATA_FOLDER = "data"
MARK_SCHEME_FOLDER = "mark_scheme"
QUESTION_PAPERS_FOLDER = "question_papers"
MERGED_FOLDER = "MERGED"
MERGED_FILE = "merged.pdf"
MERGED_TEMP_FILE = "merged_temp.pdf"

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
