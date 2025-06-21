# BlitzTape - RÚV Scraper

This project contains Python scripts for downloading video series from the RÚV (The Icelandic National Broadcasting Service) website.

## Core Functionality

The main script is designed to take the URL of a series on the RÚV website and download all of its available episodes.

Key features include:
-   **Series-Specific Folders**: It automatically creates a directory named after the series title to store the downloads.
-   **Episode Naming**: Each video file is named using its specific episode title.
-   **MKV Format**: Videos are saved in the Matroska (MKV) container format.
-   **Metadata File**: A single `info.nfo` file is generated for the entire series, containing metadata for all the downloaded episodes.

## Expected Output Structure

For any given series, the script will organize the downloaded files as follows:

```
downloads/
└── <Series Title>/
    ├── <Episode 1 Title>.mkv
    ├── <Episode 2 Title>.mkv
    ├── ...
    ├── <Last Episode Title>.mkv
    └── info.nfo
```

## Usage

To use the scraper, you would run the appropriate Python script from your terminal, passing the series URL as an argument.

**Example:**

```bash
python ruv_scraper/ruv_scraper.py "URL_OF_THE_RUV_SERIES"
```
