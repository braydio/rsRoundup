# rsRoundup Script

## Overview

`rsRoundup` is designed to fetch and process recent SEC filings related to reverse splits, cash in lieu corporate actions related to reverse split with share roundup. It retrieves the data, extracts relevant excerpts, and saves the filings for further analysis.

## Features

- Fetch recent SEC filings based on specific keywords.
- Extract relevant excerpts from the filings, focusing on terms like "reverse stock split," "cash in lieu," and "preserve round lot."
- Save results and download filings in a structured format.
- Delete old files in the `filings` folder before processing new data.

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/braydio/rsRoundup.git
    ```

2. Navigate to the project directory:
    ```bash
    cd rsRoundup
    ```

3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1. Configure the script parameters in the `rsRoundup.py` file.
2. Run the script:
    ```bash
    python rsRoundup.py
    ```

## Configuration

### Script Parameters

- **Date Range**: Update the following variables in `rsRoundup.py` to define the date range for the search:
  - `START_DATE`: The start date for fetching filings (default is 7 days prior to the current date).
  - `END_DATE`: The end date for fetching filings (default is the current date).

### Search Terms

The search terms can be modified in the `SEARCH_TERMS` dictionary within `rsRoundup.py`. The current keywords are:

- `keywords`: Terms related to reverse stock splits, e.g., "reverse stock split," "no fractional shares," "reverse split."
- `in_lieu_keywords`: Terms related to cash in lieu, e.g., "in lieu."
- `preserve_round_lot_keywords`: Terms related to preserving round lots, e.g., "preserve round lot."

These terms are used to search within the SEC filings and extract relevant information.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
