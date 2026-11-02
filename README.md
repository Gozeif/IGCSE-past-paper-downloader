# IGCSE Past Paper Downloader

Download past papers and mark schemes for a whole subject in one go, then
optionally merge them into a single PDF. Papers are fetched from
[dynamicpapers.com](https://dynamicpapers.com/) and the tool works with **CIE**,
**AQA** and **Edexcel** subjects.

> Forked from [ThundR67/IGCSE-past-paper-downloader](https://github.com/ThundR67/IGCSE-past-paper-downloader)
> and rewritten to use dynamicpapers.com.

## Features

- Download a subject's question papers and mark schemes between a start and end year
- Look a subject up by paper code (`0580`, `9709`, `4MA1`, ...) or by name (`edexcel maths`)
- Exclude paper variants you don't need, for example the practical papers
- Skips files you already downloaded, so you can re-run it safely
- Removes "BLANK PAGE" pages from every PDF
- Merge all of a subject's question papers into one PDF

## Requirements

- Python 3.9 or newer
- The packages in `requirements.txt`

```
pip install -r requirements.txt
```

## Setup

The subject pages on dynamicpapers.com are password protected, so the tool needs
the site's password. It looks for it in this order:

1. The `DYNAMICPAPERS_PASSWORD` environment variable (or a `.env` file, see below)
2. If neither is set, it asks you for it when you run the script

To use a `.env` file, copy the example and fill it in:

```
cp .env.example .env        # on Windows: copy .env.example .env
```

```
DYNAMICPAPERS_PASSWORD=your-password-here
```


## Usage

Run the script from the project folder:

```
python main.py
```

### Download

1. Type `download` when asked whether to download or merge.
2. Enter a paper code or a subject name, for example `0580`, `9709`, `4MA1` or
   `edexcel maths`. If more than one subject matches, pick one (or several, or
   `all`) from the list.
3. Enter the start year and the end year.
4. Say `yes` if you want to exclude certain papers, then answer for each season
   (summer, mid-year (March), winter) and enter the variant codes to skip,
   separated by spaces. For example, to skip CIE practical papers in
   Physics, enter `51 52 53` for summer and winter, and `52` for March.
5. The papers download into the `data` folder.

Examiner reports, grade thresholds and similar files (see `BANNED_PAPER_TYPES`
in `config.py`) are always skipped.

### Merge

1. Type `merge` when asked whether to download or merge.
2. Enter the same code or name you used to download. The papers must already be
   downloaded.
3. All question papers for that subject are merged, oldest first, into one PDF.

Mark schemes are not included in the merged file.

## Where files end up

```
data/
  <code>/
    question_papers/    2019_0580_s19_qp_12.pdf, ...
    mark_scheme/        2019_0580_s19_ms_12.pdf, ...
    MERGED/
      merged.pdf        created by the merge step
```

The folder is named after what you typed, so use the same text when merging.

## Configuration

Everything you are likely to change is in `config.py`:

| Setting | What it does |
|---|---|
| `BOARD_PATHS` | Which parts of the site menu count as subjects, and which board they belong to |
| `EDEXCEL_CODES` | Maps Edexcel codes such as `4MA1` to the subject's menu name. Add your own lines for subjects that are missing |
| `BANNED_PAPER_TYPES` | File types that are never downloaded |
| `SEASONS` | The seasons you can filter by |
| `DATA_FOLDER` and the other folder names | Where downloads and merged files are stored |
| `TIMEOUT` | Seconds to wait for each request |

## Troubleshooting

- **"Invalid Paper Code"**: the code or name doesn't match any subject on the
  site. Try a name instead, or add the code to `EDEXCEL_CODES` if it's an
  Edexcel subject.
- **"is still locked - is the password correct"**: the site password is wrong or
  has changed. Check `DYNAMICPAPERS_PASSWORD`.
- **"No papers found ... see debug_page.html"**: the site's page layout is not
  what the script expects. The page it saw is saved as `debug_page.html`, which
  helps when reporting or fixing the problem.
- **"Could not strip blank pages"**: the PDF is kept as downloaded, only the
  blank-page cleanup was skipped.

## Disclaimer

The past papers belong to their exam boards and are hosted by dynamicpapers.com.
This tool is meant for personal study use only. Please be considerate and don't
hammer the site with repeated large downloads.

## License

MIT, see [LICENSE](LICENSE).
