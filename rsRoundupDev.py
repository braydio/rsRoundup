import requests
import yfinance as yf
from datetime import datetime, timedelta
import re
import time
import os
import json
from bs4 import BeautifulSoup
import pdfkit
import fitz

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
def write_results_to_file(results, filename='output.txt'):
    unique_file_numbers = set()

    # Create a mapping for neatly printing the field names
    field_name_mapping = {
        #'file_number': 'File Number',
        #'accession_number': 'Accession Number',
        'display_names': 'Company Info',
        'form_type': 'Form Type',
        'primary_doc_description': 'Description',
        'file_date': 'File Date',
        'period_ending': 'Period Ending',
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

def add_annotation_to_pdf(pdf_file, excerpt_links):
    try:
        doc = fitz.open(pdf_file)
        for link in excerpt_links:
            page_num = link['page']
            start_pos = link['start']
            end_pos = link['end']
            link_text = link['text']

            page = doc.load_page(page_num)
            # Assume a basic approach to find the text position. Adjust as necessary.
            text_instances = page.search_for(link_text)
            
            if text_instances:
                for inst in text_instances:
                    # Create a link annotation
                    rect = fitz.Rect(inst[:2] + (inst[2], inst[3]))
                    page.add_link(rect=rect, uri="http://example.com")  # Use real URI if needed
            else:
                print(f"Text '{link_text}' not found on page {page_num}")

        doc.save(pdf_file)
        print(f"Annotations added to {pdf_file}")

    except Exception as e:
        print(f"Error adding annotations: {e}")

def save_excerpt(excerpt, company_name, form_type, destination_folder='filings'):
    """
    Save the relevant excerpt as a .txt file.
    """
    try:
        os.makedirs(destination_folder, exist_ok=True)  # Create folder if it doesn't exist

        # Construct the filename
        sanitized_company_name = re.sub(r'[\\/*?:"<>|]', "", company_name)  # Remove invalid characters
        filename = f"{sanitized_company_name}, {form_type} - Excerpt.txt"
        filepath = os.path.join(destination_folder, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(excerpt)

        print(f"Excerpt saved: {filepath}")
        return filepath
    except Exception as e:
        print(f"Error saving excerpt: {e}")
        return None

def extract_relevant_excerpt(result, filing_url, company_name, form_type):
    """
    Extract relevant excerpts from the filing based on specific keywords or patterns.
    Includes links to the PDF version of the document.
    """
    try:
        response = requests.get(filing_url, headers=headers)
        response.raise_for_status()
        
        # Parse HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        text_content = soup.get_text()
        
        # Define the keywords or patterns to look for
        keywords = ["reverse stock split", "no fractional shares", "reverse split"]
        in_lieu_keywords = ["in lieu"]

        # Split the text content into lines for line number tracking
        lines = text_content.split('\n')
        
        excerpts = []
        in_lieu_excerpts = []

        for line_number, line in enumerate(lines, start=1):
            line_lower = line.lower()
            # Check for keywords for general excerpts
            for keyword in keywords:
                if keyword.lower() in line_lower:
                    # Shorten the excerpt to include a snippet around the keyword
                    start = max(line_lower.find(keyword.lower()) - 50, 0)
                    end = min(line_lower.find(keyword.lower()) + len(keyword) + 50, len(line))
                    snippet = line[start:end].strip()
                    excerpts.append(f"Line {line_number}: {snippet}")
            # Check for 'in lieu' for the specific flag
            for in_lieu_keyword in in_lieu_keywords:
                if in_lieu_keyword.lower() in line_lower:
                    start = max(line_lower.find(in_lieu_keyword.lower()) - 30, 0)
                    end = min(line_lower.find(in_lieu_keyword.lower()) + len(in_lieu_keyword) + 30, len(line))
                    snippet = line[start:end].strip()
                    in_lieu_excerpts.append(f"Line {line_number}: {snippet}")

        # Define file names
        excerpt_filename = os.path.join('filings', f"{company_name}, {form_type} - Excerpt.txt")
        in_lieu_filename = os.path.join('filings', f"{company_name}, {form_type} - In Lieu Flag.txt")
        
        # Save excerpt if found
        if excerpts:
            os.makedirs('filings', exist_ok=True)  # Ensure the 'filings' directory exists
            with open(excerpt_filename, 'w', encoding='utf-8') as f:
                f.write('Relevant excerpts:\n')
                for excerpt in excerpts:
                    f.write(f"{excerpt}\n")
            print(f"Excerpt saved to {excerpt_filename}")

        # Save in-lieu flag if applicable
        if in_lieu_excerpts:
            with open(in_lieu_filename, 'w', encoding='utf-8') as f:
                f.write('Relevant excerpts with "in lieu":\n')
                for in_lieu_excerpt in in_lieu_excerpts:
                    f.write(f"{in_lieu_excerpt}\n")
            print(f"In Lieu Flag saved to {in_lieu_filename}")

    except Exception as e:
        print(f"Error extracting excerpt: {e}")

def convert_html_to_pdf(html_file, pdf_file):
    pdfkit.from_file(html_file, pdf_file)

def download_filing(filing_url, company_name, form_type, destination_folder='filings'):
    """
    Download the filing from the given URL and save it as an .htm file.
    """
    try:
        os.makedirs(destination_folder, exist_ok=True)  # Create folder if it doesn't exist

        # Construct the filename
        sanitized_company_name = re.sub(r'[\\/*?:"<>|]', "", company_name)  # Remove invalid characters
        html_filename = f"{sanitized_company_name}, {form_type} - Filing.htm"
        html_filepath = os.path.join(destination_folder, html_filename)

        response = requests.get(filing_url, headers=headers)
        response.raise_for_status()

        with open(html_filepath, 'wb') as f:
        # Convert HTML to PDF
            pdf_filename = f"{sanitized_company_name}, {form_type} - Filing.pdf"
            pdf_filepath = os.path.join(destination_folder, pdf_filename)
            convert_html_to_pdf(html_filepath, pdf_filepath)

        print(f"Filing downloaded and converted to PDF: {pdf_filepath}")
        return pdf_filepath
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
                "file_number": result['_source'].get('file_num', ['N/A'])[0],
                "accession_number": result['_source'].get('adsh', 'N/A'),  # Use ADSH as filing ID
                "form_type": form_type,
                "primary_doc_description": result['_source'].get('file_description', 'N/A'),
                "file_date": result['_source'].get('file_date', 'N/A'),
                "period_ending": result['_source'].get('period_ending', 'N/A'),
                "display_names": result['_source'].get('display_names', []),
                #"tickers": get_ticker_symbols(result['_source'].get('display_names', []))
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
    
    # Uncomment this for a raw dump from API 
    # print(json.dumps(data, indent=2))

    results = []
    if 'hits' in data and 'hits' in data['hits']:
        for result in data['hits']['hits']:
            form_type = result['_source'].get('form', 'N/A')
            if form_type in ['8-K', 'S-1', 'S-3', 'S-4', '14A', '10-K', '10-Q']:
                company_info = result['_source'].get('display_names', ['N/A'])[0]
                company_name = company_info.split('(')[0].strip()

                filing_info = {
                    "file_number": result['_source'].get('file_num', ['N/A'])[0],
                    "accession_number": result['_source'].get('adsh', 'N/A'),  # Use ADSH as filing ID
                    "form_type": form_type,
                    "primary_doc_description": result['_source'].get('file_description', 'N/A'),
                    "file_date": result['_source'].get('file_date', 'N/A'),
                    "period_ending": result['_source'].get('period_ending', 'N/A'),
                    "display_names": result['_source'].get('display_names', []),
                }

                # Construct the filing URL
                cik = result['_source'].get('ciks', [''])[0]  # Get the first CIK value
                file_id = result['_id'].split(":")[1]  # Extract the file ID from _id
                filing_info["filing_url"] = construct_filing_url(cik, filing_info["accession_number"], file_id)

                results.append(filing_info)

                # Download the filing without modification
                download_filing(filing_info["filing_url"], company_name, form_type)

                # Extract and save the excerpt
                excerpt = extract_relevant_excerpt(result, filing_info["filing_url"], company_name, form_type)

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
    print("Source filings and relevant excerpts saved.\n")
    print("See output.txt for details.")

except requests.exceptions.RequestException as e:
    with open('output.txt', 'w') as f:
        f.write(f"Request failed: {e}\n")
    print(f"Request failed: {e}")

