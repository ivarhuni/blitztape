# BlitzTape - RÚV Scraper

This project contains Python scripts for downloading video series from the RÚV (The Icelandic National Broadcasting Service) website.

## Features
- **Series-Specific Folders**: Automatically creates a directory named after the series title to store downloads.
- **Episode Naming**: Each video file is named using its specific episode title.
- **MKV Format**: Videos are saved in the Matroska (MKV) container format.
- **Metadata File**: A single `info.nfo` file is generated for the entire series, containing metadata for all downloaded episodes.
- **Resumable & Skips Existing**: Skips already-downloaded episodes and can resume interrupted downloads.
- **Download Limit**: Optionally limit the number of episodes to download.
- **Custom Output Directory**: Save downloads anywhere you like.

## Installation

### 1. Install Python dependencies

Open a terminal and run:

```bash
pip install -r ruv_scraper/requirements.txt
```

### 2. Install yt-dlp

- **Windows**: Download the latest yt-dlp.exe from [yt-dlp releases](https://github.com/yt-dlp/yt-dlp/releases) and place it somewhere in your PATH (e.g., `C:\Windows\System32` or the project folder). Or install via pip:
  ```bash
  pip install -U yt-dlp
  ```
- **Mac**: Install via Homebrew (recommended):
  ```bash
  brew install yt-dlp
  ```
  Or via pip:
  ```bash
  pip install -U yt-dlp
  ```

## Usage

Run the scraper from the project root or the `ruv_scraper` directory:

```bash
python ruv_scraper/ruv_improved_scraper.py <series_url> [--limit <number_of_episodes>] [--output-dir <directory>]
```

- `<series_url>`: The URL of the RÚV series page (required)
- `--limit <number_of_episodes>`: (Optional) Download only the first N episodes
- `--output-dir <directory>`: (Optional) Set a custom output directory (default: `ruv_scraper/downloads`)

### Example 1: Download the entire series "Bubbi byggir"

```bash
python ruv_scraper/ruv_improved_scraper.py "https://www.ruv.is/sjonvarp/spila/bubbi-byggir/37750/b80cbg" --output-dir ruv_scraper/test_downloads
```

### Example 2: Download the entire series "Sammi brunavörður X"

```bash
python ruv_scraper/ruv_improved_scraper.py "https://www.ruv.is/sjonvarp/spila/sammi-brunavordur-x/37768/b85s4f" --output-dir ruv_scraper/test_downloads
```

## Output Structure

For any given series, the script organizes the downloaded files as follows:

```
<output-dir>/
└── <Series Title>/
    ├── <Episode 1 Title>.mkv
    ├── <Episode 2 Title>.mkv
    ├── ...
    └── info.nfo
```

- All episodes are saved as `.mkv` files.
- A single `info.nfo` file contains metadata for all episodes in the series.

## Notes
- Make sure `yt-dlp` is installed and available in your system PATH.
- The script is tested on both Windows 10 and macOS.
- If you encounter issues, ensure all dependencies are installed and up to date.
