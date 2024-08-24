import requests
import yfinance as yf
from datetime import datetime, timedelta
import re
import time
import os
import json

print("               ____                        __           ")
print("    __________/ __ \\____  __  ______  ____/ /_  ______  ")
print("   / ___/ ___/ /_/ / __ \\/ / / / __ \\/ __  / / / / __ \\ ")
print("  / /  (__  ) _, _/ /_/ / /_/ / / / / /_/ / /_/ / /_/ / ")
print(" /_/  /____/_/ |_|\\____/\\__,_/_/ /_/\\__,_/\\__,_/ .___/  ")
print("                                               /_/      ")

print("rsRoundup script v1.0 created by @Braydio")
print("Contributions by @echo and @ckzz on Xtrades")
print("https://github.com/bchaffee23/rsRoundup\n\n")


# --- Configuration ---
url = "https://efts.sec.gov/LATEST/search-index"
end_date = datetime.today().strftime('%Y-%m-%d')
start_date = (datetime.today() - timedelta(days=7)).strftime('%Y-%m-%d')
params = {
    "q": "\"reverse split\" AND \"fractional shares\" OR \"Rounded Up\" OR \"rounding\"",
    "dateRange": "custom",
    "startdt": start_date,
    "enddt": end_date,
    "category": "full",
    "start": 0,
    "count": 100
}

# Headers
headers = {"User-Agent": "MyApp/1.0 (my.email@example.com)"}

# --- Functions ---
def get_ticker_symbols(display_names):
    tickers = []
    for name in display_names:
        match = re.search(r"\(([^)]+)\)", name)  # Find text within parentheses
        if match:
            tickers.extend(match.group(1).replace(",", "").split())
    return tickers

def get_current_price(ticker):
    try:
        ticker_info = yf.Ticker(ticker).info
        # Use previousClose if market is closed
        price_key = 'regularMarketPrice' if 'regularMarketPrice' in ticker_info else 'previousClose' 
        return ticker_info[price_key] if price_key in ticker_info else "N/A"
    except Exception as e:  
        print(f"Error fetching price for {ticker}: {e}")  
        return "N/A"

def write_results_to_file(results, filename='output.txt'):
    unique_file_numbers = set()

    # Create a mapping for neatly printing the field names
    field_name_mapping = {
        'file_number': 'File Number',
        'accession_number': 'Accession Number',
        'form_type': 'Form Type',
        'primary_doc_description': 'Description',
        'file_date': 'File Date',
        'period_ending': 'Period Ending',
        'display_names': 'Company Info',
        'filing_url': 'Filing URL',
    } 

    with open(filename, 'w') as f:
        f.write(f"Total Unique Results: {len(results)}\n\n")  # Count unique results
        for result in results:
            # Check if file number is already processed
            if result['file_number'] not in unique_file_numbers: 
                unique_file_numbers.add(result['file_number'])

                for key, value in result.items():
                    # Use the field name mapping to print human-readable field names
                    field_name = field_name_mapping.get(key, key).capitalize()
                    f.write(f"{field_name}: {value}\n")

                # Display Ticker Price
                if result['tickers']:
                    ticker_price = get_current_price(result['tickers'][0])  
                    f.write(f"Current Price (as of {datetime.now().strftime('%Y-%m-%d')}): {ticker_price}\n\n")
                    tradingview_url = f"https://www.tradingview.com/chart/?symbol={result['tickers'][0]}"
                    f.write(f"TradingView URL: {tradingview_url}\n\n")
                else:
                    f.write("Current Price: N/A\n\n") 
                    f.write("TradingView URL: N/A\n\n")

def download_filing(filing_url, destination_folder='filings'):
    """
    (Trying to) Download the filing from the given URL and save it to the specified folder.
    """
    try:
        os.makedirs(destination_folder, exist_ok=True)  # Create folder if not exists
        filename = filing_url.split("/")[-1]
        filepath = os.path.join(destination_folder, filename)

        response = requests.get(filing_url, headers=headers)
        response.raise_for_status()

        with open(filepath, 'w') as f:
            f.write(response.text)
        
        print(f"Filing downloaded: {filepath}")
        return filepath
    except Exception as e:
        print(f"Error downloading filing: {e}")
        return None

def get_recent_filings(cik, company_name):
    """
    Fetch recent filings for a given CIK and return the most recent ones.
    """
    filings_url = "https://efts.sec.gov/LATEST/search-index"
    filings_params = {
        "q": f"cik:{cik}",
        "dateRange": "custom",
        "startdt": start_date,
        "enddt": end_date,
        "category": "full",
        "start": 0,
        "count": 10
    }

    try:
        filings_response = requests.get(filings_url, params=filings_params, headers=headers)
        filings_response.raise_for_status()
        filings_data = filings_response.json()

        recent_filings = []
        if 'hits' in filings_data and 'hits' in filings_data['hits']:
            for filing in filings_data['hits']['hits']:
                filing_info = {
                    "form_type": filing['_source'].get('form', 'N/A'),
                    "file_date": filing['_source'].get('file_date', 'N/A'),
                    "description": filing['_source'].get('file_description', 'N/A'),
                    "accession_number": filing['_source'].get('adsh', 'N/A')
                }
                recent_filings.append(filing_info)
                # Generate link for the filing
                accession_number = filing_info['accession_number']
                filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number.replace('-', '')}/{accession_number}.txt"
                filing_info["filing_url"] = filing_url

        return recent_filings

    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch recent filings for {company_name}: {e}")
        return []

def construct_filing_url(cik, adsh, file_id):
    base_url = "https://www.sec.gov/Archives/edgar/data/"
    return f"{base_url}{cik}/{adsh.replace('-', '')}/{file_id}"

def delete_old_files(directory='filings'):
    """
    Confirm and delete all files in the specified directory.
    """
    try:
        files = os.listdir(directory)
        if files:
            confirm = input(f"{len(files)} files found in '{directory}'. Do you want to delete them? (yes/no): ")
            if confirm.lower() == 'yes':
                for file in files:
                    file_path = os.path.join(directory, file)
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")
            else:
                print("Skipping file deletion.")
        else:
            print("No files to delete.")
    except FileNotFoundError:
        print(f"Directory '{directory}' not found, creating it...")
        os.makedirs(directory, exist_ok=True)

# --- Main Script ---
delete_old_files('filings')  # Confirm and delete old files before running

try:
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    data = response.json()
    print(json.dumps(data, indent=2))

    results = []
    if 'hits' in data and 'hits' in data['hits']:
        for result in data['hits']['hits']:
            form_type = result['_source'].get('form', 'N/A')
            if form_type in ['8-K', 'S-1', 'S-3', 'S-4']:
                filing_info = {
                    "file_number": result['_source'].get('file_num', ['N/A'])[0],
                    "accession_number": result['_source'].get('adsh', 'N/A'),  # Use ADSH as filing ID
                    "form_type": form_type,
                    "primary_doc_description": result['_source'].get('file_description', 'N/A'),
                    "file_date": result['_source'].get('file_date', 'N/A'),
                    "period_ending": result['_source'].get('period_ending', 'N/A'),
                    "display_names": result['_source'].get('display_names', []),
                    "tickers": get_ticker_symbols(result['_source'].get('display_names', []))
                }

                # Construct the filing URL
                cik = result['_source'].get('ciks', [''])[0]  # Get the first CIK value
                file_id = result['_id'].split(":")[1]  # Extract the file ID from _id
                filing_info["filing_url"] = construct_filing_url(cik, filing_info["accession_number"], file_id)

                results.append(filing_info)

                # Optionally download the filing
                download_filing(filing_info["filing_url"])

    # Process results, remove duplicates, etc.
    results = list({r['file_number']: r for r in results}.values()) 
    filtered_results = filter(lambda x: 'file_date' in x, results)

    sorted_results = sorted(
        filtered_results, 
        key=lambda x: datetime.strptime(x['file_date'], '%Y-%m-%d') if 'file_date' in x else datetime.min,  
        reverse=True
    )
    write_results_to_file(sorted_results)

    print(f"\nrsRoundup located {len(sorted_results)} filings...\n")
    print("Results are saved to 'output.txt'\n")
    print("Filings  saved in master.zip\n")

except requests.exceptions.RequestException as e:
    with open('output.txt', 'w') as f:
        f.write(f"Request failed: {e}\n")
    print(f"Request failed: {e}")
