"""Configurations For IGCSE Past Papers Downloader"""

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 5.1.1; SM-G928X Build/LMY47X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.83 Mobile Safari/537.36'
}



# --- Folders / files ----------------------------------------------------
DATA_FOLDER = "data"
MARK_SCHEME_FOLDER = "mark_scheme"
QUESTION_PAPERS_FOLDER = "question_papers"
MERGED_FOLDER = "MERGED"
MERGED_FILE = "merged.pdf"
MERGED_TEMP_FILE = "merged_temp.pdf"

BASE_URL = "https://www.cienotes.com/cie-igcse-past-papers/"
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
