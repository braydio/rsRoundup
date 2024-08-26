# rsRoundup Script

## Overview

The `rsRoundup` script is designed to fetch and process recent SEC filings related to reverse splits and rounding. It retrieves the data, processes ticker symbols, and provides current stock prices.

## Features

- Fetch recent SEC filings based on specific criteria.
- Extract ticker symbols from filings.
- Retrieve current stock prices.
- Save results to a file and downloads the filings.

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/rsRoundup.git
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

1. Configure the script parameters in the `autoRSA.py` file.
2. Run the script:
    ```bash
    python autoRSA.py
    ```

## Configuration

Update the following variables in `autoRSA.py`:

- `start_date` and `end_date`: Define the date range for the search.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
