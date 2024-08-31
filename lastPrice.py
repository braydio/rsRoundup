# Get ticker, current price, 

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

    # Display Ticker Price
    if result['tickers']:
        ticker_price = get_current_price(result['tickers'][0])  
        f.write(f"Current Price (as of {datetime.now().strftime('%Y-%m-%d')}): {ticker_price}\n\n")
        tradingview_url = f"https://www.tradingview.com/chart/?symbol={result['tickers'][0]}"
        f.write(f"TradingView URL: {tradingview_url}\n\n")
    else:
        f.write("Current Price: N/A\n\n") 
        f.write("TradingView URL: N/A\n\n")