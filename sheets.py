import requests
import pandas as pd
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# API URL for fetching top 50 cryptocurrencies (CoinGecko API)
API_URL = "https://api.coingecko.com/api/v3/coins/markets"
PARAMS = {
    "vs_currency": "usd",
    "order": "market_cap_desc",
    "per_page": 50,
    "page": 1,
    "sparkline": False,
}

# Google Sheets Authentication
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDENTIALS_FILE = "/Users/mansibali/Downloads/assessment-452718-ead0bd5fd7f9.json"  # Replace with your JSON credentials file
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPE)
client = gspread.authorize(creds)
SPREADSHEET_NAME = "Live Crypto Data"


# Function to fetch live cryptocurrency data
def fetch_crypto_data():
    response = requests.get(API_URL, params=PARAMS)
    if response.status_code == 200:
        data = response.json()
        return pd.DataFrame([{
            "Name": coin["name"],
            "Symbol": coin["symbol"].upper(),
            "Current Price (USD)": coin["current_price"],
            "Market Cap": coin["market_cap"],
            "24h Volume": coin["total_volume"],
            "24h Change (%)": coin["price_change_percentage_24h"]
        } for coin in data])
    else:
        print("Error fetching data")
        return pd.DataFrame()


# Function to perform data analysis
def analyze_data(df):
    if df.empty:
        return None

    top_5 = df.nlargest(5, "Market Cap")
    avg_price = df["Current Price (USD)"].mean()
    max_change = df["24h Change (%)"].max()
    min_change = df["24h Change (%)"].min()

    analysis = {
        "Top 5 Cryptos by Market Cap": top_5.to_dict(orient='records'),
        "Average Price of Top 50": avg_price,
        "Max 24h Change (%)": max_change,
        "Min 24h Change (%)": min_change,
    }
    return analysis


# Function to save live data to Google Sheets
def save_to_google_sheets(df, analysis):
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)
    except gspread.exceptions.SpreadsheetNotFound:
        spreadsheet = client.create(SPREADSHEET_NAME)
        spreadsheet.share(creds.service_account_email, perm_type='user', role='writer')

    # Create or select "Live Data" sheet
    try:
        sheet_data = spreadsheet.worksheet("Live Data")
    except gspread.exceptions.WorksheetNotFound:
        sheet_data = spreadsheet.add_worksheet(title="Live Data", rows="100", cols="10")

    # Clear and update "Live Data" sheet
    sheet_data.clear()
    sheet_data.append_row(["Name", "Symbol", "Current Price (USD)", "Market Cap", "24h Volume", "24h Change (%)"],
                          value_input_option="USER_ENTERED")
    sheet_data.append_rows(df.values.tolist(), value_input_option="USER_ENTERED")

    # Apply formatting to header
    sheet_data.format("A1:F1",
                      {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}})

    # Auto-adjust column widths
    sheet_data.format("A:F", {"wrapStrategy": "WRAP", "horizontalAlignment": "CENTER"})

    # Conditional formatting for 24h Change (%) - Red for negative, Green for positive
    sheet_data.format("F2:F", {
        "textFormat": {"bold": True},
        "backgroundColorStyle": {"rgbColor": {"red": 1.0, "green": 0.6, "blue": 0.6}},  # Light red for negative
        "numberFormat": {"type": "NUMBER", "pattern": "0.00%"}
    })

    # Create or select "Analysis" sheet
    try:
        sheet_analysis = spreadsheet.worksheet("Analysis")
    except gspread.exceptions.WorksheetNotFound:
        sheet_analysis = spreadsheet.add_worksheet(title="Analysis", rows="20", cols="10")

    # Clear and update "Analysis" sheet
    sheet_analysis.clear()
    sheet_analysis.append_row(["Analysis"], value_input_option="USER_ENTERED")
    sheet_analysis.append_row(["Top 5 Cryptos by Market Cap"])

    for coin in analysis["Top 5 Cryptos by Market Cap"]:
        sheet_analysis.append_row([coin["Name"], f"${coin['Market Cap']:,}"])

    sheet_analysis.append_row(["Average Price of Top 50", f"${analysis['Average Price of Top 50']:.2f}"])
    sheet_analysis.append_row(["Max 24h Change (%)", f"{analysis['Max 24h Change (%)']:.2f}%"])
    sheet_analysis.append_row(["Min 24h Change (%)", f"{analysis['Min 24h Change (%)']:.2f}%"])

    # Apply formatting to Analysis sheet
    sheet_analysis.format("A1:B1", {"textFormat": {"bold": True, "fontSize": 14}})
    sheet_analysis.format("A2:B20", {"horizontalAlignment": "CENTER"})

    print("Google Sheets updated successfully with formatted data and analysis.")


# Main function to fetch, analyze, and save data
def main():
    while True:
        print("Fetching live cryptocurrency data...")
        df = fetch_crypto_data()
        analysis = analyze_data(df)

        if analysis:
            print("Analysis:", analysis)  # Keep printing for debugging
            save_to_google_sheets(df, analysis)

        print("Waiting for the next update...")
        time.sleep(300)  # Update every 5 minutes



if __name__ == "__main__":
    main()
