import requests
import os
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# --- Configuration ---
BASE_URL = "https://efts.sec.gov/LATEST/search-index"
HEADERS = {"User-Agent": "MyApp/1.0 (my.email@example.com)"}
START_DATE = (datetime.today() - timedelta(days=2)).strftime('%Y-%m-%d') # 5 day search window
END_DATE = datetime.today().strftime('%Y-%m-%d')
DEFAULT_OUTPUT_FILE = 'output.txt'
DEFAULT_FILINGS_FOLDER = 'filings'

# Search and excerpt terms
SEARCH_TERMS = {
    "keywords": ["reverse stock split", "no fractional shares", "reverse split"],
    "in_lieu_keywords": ["in lieu"],
    "preserve_round_lot_keywords": ["preserve round lot"]
}

def display_intro():
    intro_text = """
               ____                        __           
    __________/ __ \\____  __  ______  ____/ /_  ______  
   / ___/ ___/ /_/ / __ \\/ / / / __ \\/ __  / / / / __ \\ 
  / /  (__  ) _, _/ /_/ / /_/ / / / / /_/ / /_/ / /_/ / 
 /_/  /____/_/ |_|\\____/\\__,_/_/ /_/\\__,_/\\__,_/ .___/  
                                               /_/      

rsRoundup script v1.0 created by @Braydio
Contributions by @echo and @ckzz on Xtrades
https://github.com/bchaffee23/rsRoundup

"""
    print(intro_text)

def get_search_params():
    return {
        "q": " OR ".join([
            f"\"{term}\"" for term in SEARCH_TERMS["keywords"]
        ]) + " OR " + " OR ".join([
            f"\"{term}\"" for term in SEARCH_TERMS["in_lieu_keywords"]
        ]) + " OR " + " OR ".join([
            f"\"{term}\"" for term in SEARCH_TERMS["preserve_round_lot_keywords"]
        ]),
        "dateRange": "custom",
        "startdt": START_DATE,
        "enddt": END_DATE,
        "category": "full",
        "start": 0,
        "count": 100
    }

def write_results_to_file(results, filename=DEFAULT_OUTPUT_FILE):
    field_name_mapping = {
        'display_names': 'Company Info',
        'form_type': 'Form Type',
        'primary_doc_description': 'Description',
        'file_date': 'File Date',
        'period_ending': 'Period Ending',
        'in_lieu_flag': 'Cash in Lieu: ',
    }
    
    with open(filename, 'w') as f:
        f.write(f"Total Unique Results: {len(results)}\n\n")
        for result in results:
            f.write("===========================================\n")
            # Printing the fields in the required order
            f.write(f"{field_name_mapping['display_names']}: {result.get('display_names', 'N/A')}\n")
            f.write(f"{field_name_mapping['form_type']}: {result.get('form_type', 'N/A')}\n")
            f.write(f"{field_name_mapping['primary_doc_description']}: {result.get('primary_doc_description', 'N/A')}\n")
            f.write(f"{field_name_mapping['file_date']}: {result.get('file_date', 'N/A')}\n")
            f.write(f"{field_name_mapping['period_ending']}: {result.get('period_ending', 'N/A')}\n")
            
            # Check for the 'in lieu' flag and print it
            in_lieu = "LIKELY CASH-IN-LIEU - SEE EXCERPT" if 'in_lieu_flag' in result else "N/A"
            f.write(f"{field_name_mapping['in_lieu_flag']}{in_lieu}\n")
            
            f.write("===========================================\n")
            f.write("\n")

def save_excerpt(excerpt, company_name, form_type, destination_folder=DEFAULT_FILINGS_FOLDER):
    try:
        os.makedirs(destination_folder, exist_ok=True)
        sanitized_company_name = re.sub(r'[\\/*?:"<>|]', "", company_name)
        filename = f"{sanitized_company_name}, {form_type} - Excerpt.txt"
        filepath = os.path.join(destination_folder, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(excerpt)

        print(f"Excerpt saved: {filepath}")
        return filepath
    except Exception as e:
        print(f"Error saving excerpt: {e}")
        return None

def extract_relevant_excerpt(filing_url, company_name, form_type):
    try:
        response = requests.get(filing_url, headers=HEADERS)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        text_content = soup.get_text()
        
        lines = text_content.split('\n')
        excerpts = []
        in_lieu_excerpts = []
        round_lot_excerpts = []
        cash_in_lieu_flag = False
        round_lot_flag = False

        for line_number, line in enumerate(lines, start=1):
            line_lower = line.lower()
            for keyword in SEARCH_TERMS["keywords"]:
                if keyword.lower() in line_lower:
                    start = max(line_lower.find(keyword.lower()) - 50, 0)
                    end = min(line_lower.find(keyword.lower()) + len(keyword) + 50, len(line))
                    snippet = line[start:end].strip()
                    excerpts.append(f"Line {line_number}: {snippet}")

            for in_lieu_keyword in SEARCH_TERMS["in_lieu_keywords"]:
                if in_lieu_keyword.lower() in line_lower:
                    start = max(line_lower.find(in_lieu_keyword.lower()) - 50, 0)
                    end = min(line_lower.find(in_lieu_keyword.lower()) + len(in_lieu_keyword) + 50, len(line))
                    snippet = line[start:end].strip()
                    in_lieu_excerpts.append(f"Line {line_number}: {snippet}")
                    cash_in_lieu_flag = True  # Set the flag if "in lieu" is found
                
            for preserve_round_lot in SEARCH_TERMS["preserve_round_lot_keywords"]:
                if preserve_round_lot.lower() in line_lower:
                    start = max(line_lower.find(preserve_round_lot.lower()) - 50, 0)
                    end = min(line_lower.find(preserve_round_lot.lower()) + len(preserve_round_lot) + 50, len(line))
                    snippet = line[start:end].strip()
                    round_lot_excerpts.append(f"Line {line_number}: {snippet}")
                    round_lot_flag = True  # Set the flag if "preserve round lot" is found

        if excerpts:
            excerpt_filename = os.path.join('filings', f"{company_name}, {form_type} - Excerpt.txt")
            os.makedirs('filings', exist_ok=True)
            with open(excerpt_filename, 'w', encoding='utf-8') as f:
                f.write('Relevant excerpts:\n')
                for excerpt in excerpts:
                    f.write(f"{excerpt}\n")
            print(f"Excerpt saved to {excerpt_filename}")

        if round_lot_excerpts:
            roundlot_filename = os.path.join('filings', f"{company_name}, {form_type} - Round Lot.txt")
            with open(roundlot_filename, 'w', encoding='utf-8') as f:
                f.write('Relevant excerpts with "preserve round lot":\n')
                for round_lot_excerpt in round_lot_excerpts:
                    f.write(f"{round_lot_excerpt}\n")
            print(f"Round Lot Flag saved to {roundlot_filename}")

        if in_lieu_excerpts:
            in_lieu_filename = os.path.join('filings', f"{company_name}, {form_type} - In Lieu Flag.txt")
            with open(in_lieu_filename, 'w', encoding='utf-8') as f:
                f.write('Relevant excerpts with "in lieu":\n')
                for in_lieu_excerpt in in_lieu_excerpts:
                    f.write(f"{in_lieu_excerpt}\n")
            print(f"In Lieu Flag saved to {in_lieu_filename}")

        return cash_in_lieu_flag

    except Exception as e:
        print(f"Error extracting excerpt: {e}")
        return False  # Return False if there was an error

def download_filing(filing_url, company_name, form_type, destination_folder=DEFAULT_FILINGS_FOLDER):
    try:
        os.makedirs(destination_folder, exist_ok=True)
        sanitized_company_name = re.sub(r'[\\/*?:"<>|]', "", company_name)
        filename = f"{sanitized_company_name}, {form_type} - Filing.htm"
        filepath = os.path.join(destination_folder, filename)

        response = requests.get(filing_url, headers=HEADERS)
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            f.write(response.content)

        print(f"Filing downloaded: {filepath}")
        return filepath
    except Exception as e:
        print(f"Error downloading filing: {e}")
        return None

def construct_filing_url(cik, adsh, file_id):
    base_url = "https://www.sec.gov/Archives/edgar/data/"
    return f"{base_url}{cik}/{adsh.replace('-', '')}/{file_id}"

def delete_old_files(directory=DEFAULT_FILINGS_FOLDER):
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

def process_filings(data):
    results = []
    if 'hits' in data and 'hits' in data['hits']:
        for result in data['hits']['hits']:
            form_type = result['_source'].get('form', 'N/A')
            if form_type in ['8-K', 'S-1', 'S-3', 'S-4', '14A', '10-K', '10-Q']:
                company_info = result['_source'].get('display_names', ['N/A'])[0]
                company_name = company_info.split('(')[0].strip()

                filing_info = {
                    "file_number": result['_source'].get('file_num', ['N/A'])[0],
                    "accession_number": result['_source'].get('adsh', 'N/A'),
                    "form_type": form_type,
                    "primary_doc_description": result['_source'].get('file_description', 'N/A'),
                    "file_date": result['_source'].get('file_date', 'N/A'),
                    "period_ending": result['_source'].get('period_ending', 'N/A'),
                    "display_names": result['_source'].get('display_names', []),
                }

                cik = result['_source'].get('ciks', [''])[0]
                file_id = result['_id'].split(":")[1]
                filing_info["filing_url"] = construct_filing_url(cik, filing_info["accession_number"], file_id)

                # Extract relevant excerpts and determine if "cash in lieu" flag should be set
                cash_in_lieu_flag = extract_relevant_excerpt(filing_info["filing_url"], company_name, form_type)
                filing_info["in_lieu_flag"] = "Yes" if cash_in_lieu_flag else "No"

                results.append(filing_info)

                download_filing(filing_info["filing_url"], company_name, form_type)

    return results

def main():
    display_intro()
    delete_old_files(DEFAULT_FILINGS_FOLDER)
    
    search_params = get_search_params()
    try:
        response = requests.get(BASE_URL, params=search_params, headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        results = process_filings(data)
        unique_results = list({r['file_number']: r for r in results}.values())
        write_results_to_file(unique_results)

        print(f"Results have been written to {DEFAULT_OUTPUT_FILE}.")
    except Exception as e:
        print(f"An error occurred during the process: {e}")

if __name__ == "__main__":
    main()
