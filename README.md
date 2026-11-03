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
- Removes "BLANK PAGE" pages from PDFs (can be turned off)
- Merge all of a subject's question papers into one PDF
- A `settings.txt` file for your password and preferences
- Can be built into a single Windows `.exe`

## Getting started

There are two ways to run it.

**Windows exe:** download `IGCSE-Downloader.exe` from the
[Releases](../../releases) page, put it in a folder of its own and double-click
it. Nothing else needs to be installed. Windows may warn about an unknown
publisher the first time, see [Troubleshooting](#troubleshooting).

**From source:** you need Python 3.9 or newer.

```
pip install -r requirements.txt
python main.py
```

The first time you run it, the program creates a `settings.txt` file next to
itself (next to the exe, or next to `main.py`) and then carries on as normal.

## Settings

Your password and preferences live in `settings.txt`, in the same folder as the
program. Open it in Notepad, change what you need and save it. The changes apply
the next time you start the program.

```
[settings]
password =
downloads_folder = IGCSE downloads
skip_types = ir gt er pef
remove_blank_pages = yes
timeout = 60
```

| Setting | What it does | Default |
|---|---|---|
| `password` | The password for dynamicpapers.com. Leave it empty to be asked when it is needed | empty |
| `downloads_folder` | Where papers are saved. A plain name is created next to the program, or give a full path such as `D:\Papers` | `IGCSE downloads` |
| `skip_types` | File types that are never downloaded (examiner reports, grade thresholds, ...), separated by spaces. Leave empty to download everything | `ir gt er pef` |
| `remove_blank_pages` | `yes` or `no`: remove "BLANK PAGE" pages from downloaded and merged PDFs | `yes` |
| `timeout` | Seconds to wait for the site before giving up on a request | `60` |

Lines starting with `#` are comments. A setting you delete falls back to its
default. If the file can't be read, the program tells you what is wrong.

### The site password

The subject pages on dynamicpapers.com are password protected. The program looks
for the password in this order:

1. The `DYNAMICPAPERS_PASSWORD` environment variable
2. The `password` line in `settings.txt`
3. If neither is set, it asks you when it is needed

The password is stored as plain text in `settings.txt`, so don't share that file.

To use the environment variable instead:

```
# PowerShell, this session only
$env:DYNAMICPAPERS_PASSWORD = "your-password-here"

# bash / zsh
export DYNAMICPAPERS_PASSWORD="your-password-here"
```


## Usage

Start the program and answer the prompts.

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
5. The papers download into the `IGCSE downloads` folder.

### Merge

1. Type `merge` when asked whether to download or merge.
2. Enter the same code or name you used to download. The papers must already be
   downloaded.
3. All question papers for that subject are merged, oldest first, into one PDF.

Mark schemes are not included in the merged file.

## Where files end up

Everything is saved in the `IGCSE downloads` folder next to the program (or the
folder you set in `settings.txt`):

```
IGCSE downloads/
  <code>/
    question_papers/    2019_0580_s19_qp_12.pdf, ...
    mark_scheme/        2019_0580_s19_ms_12.pdf, ...
    MERGED/
      merged.pdf        created by the merge step
```

The folder is named after what you typed, so use the same text when merging.

## More configuration

Options you are less likely to need are in `config.py` (when running from source):

| Setting | What it does |
|---|---|
| `BOARD_PATHS` | Which parts of the site menu count as subjects, and which board they belong to |
| `EDEXCEL_CODES` | Maps Edexcel codes such as `4MA1` to the subject's menu name. Add your own lines for subjects that are missing |
| `SEASONS` | The seasons you can filter by |
| The folder and file names | The names of the `question_papers`, `mark_scheme` and `MERGED` folders |

## Building the exe

You need to build on Windows, with Python 3.9 or newer. Use a clean virtual
environment so the exe doesn't include unrelated packages:

```
python -m venv .venv-build
.venv-build\Scripts\Activate.ps1
pip install -r requirements.txt pyinstaller
pyinstaller --onefile --name IGCSE-Downloader main.py
```

The result is `dist\IGCSE-Downloader.exe`. Keep it as a console program (don't
use `--noconsole`), because everything runs through prompts.

If something doesn't work, these options usually help:

| Problem | Add to the `pyinstaller` command |
|---|---|
| The `fontTools` warning appears in the exe | `--collect-submodules fontTools` |
| "Couldn't find a tree builder with the features you requested: lxml" | `--collect-all lxml` |
| Slow start, or antivirus flags the single-file exe | use `--onedir` instead of `--onefile`, then zip the `dist\IGCSE-Downloader` folder |

Before sharing the exe:

- Run it from a different folder than the project, with and without a
  `settings.txt`, to check that the settings file and the downloads folder end
  up next to the exe.
- Don't bundle `settings.txt` or a password into the exe (don't use
  `--add-data` for them). Anyone who runs it gets their own `settings.txt`.
- Don't commit `dist\` or `build\`. Attach the exe to a GitHub Release instead.

## Troubleshooting

- **"Invalid Paper Code"**: the code or name doesn't match any subject on the
  site. Try a name instead, or add the code to `EDEXCEL_CODES` if it's an
  Edexcel subject.
- **"is still locked - is the password correct"**: the site password is wrong or
  has changed. Check the `password` line in `settings.txt` and the
  `DYNAMICPAPERS_PASSWORD` variable (the variable wins if both are set).
- **"settings.txt is not formatted correctly" or similar**: the file must start
  with a `[settings]` line and use `name = value` lines. Delete the file to get
  a fresh one on the next run.
- **"No papers found ... see debug_page.html"**: the site's page layout is not
  what the script expects. The page it saw is saved as `debug_page.html` next to
  the program, which helps when reporting or fixing the problem.
- **"Could not strip blank pages"**: the PDF is kept as downloaded, only the
  blank-page cleanup was skipped.
- **"fontTools is required ... but is not installed"**: install it with
  `pip install fonttools` (it is in `requirements.txt`). The program still
  works without it, but a few blank pages may be missed. In an exe built
  without it, rebuild with `--collect-submodules fontTools`.
- **Windows says "Windows protected your PC"**: the exe isn't code signed. Click
  "More info", then "Run anyway", or build it yourself from source.

## Disclaimer

The past papers belong to their exam boards and are hosted by dynamicpapers.com.
This tool is meant for personal study use only. Please be considerate and don't
hammer the site with repeated large downloads.

## License

MIT, see [LICENSE](LICENSE).
