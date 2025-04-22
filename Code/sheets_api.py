from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# Google Sheets API Configuration
SERVICE_ACCOUNT_FILE = "LOCATION REMOVED FROM HERE.json"
SPREADSHEET_ID = "API REMOVED FROM HERE"

def authenticate_google_sheets():
    """Authenticates and returns a Google Sheets API service object."""
    try:
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/spreadsheets"])
        service = build("sheets", "v4", credentials=creds)
        return service
    except Exception as e:
        print(f"❌ Error authenticating Google Sheets API: {e}")
        return None

def find_next_empty_row(service, sheet_id, sheet_name):
    """Finds the next empty row in a Google Sheets sheet."""
    try:
        sheet = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=f"{sheet_name}!A:A").execute()
        values = sheet.get("values", [])
        return len(values) + 1  # Next empty row
    except Exception as e:
        print(f"❌ Error finding next empty row: {e}")
        return None

def update_google_sheets(sheet_name, data):
    """Updates the Google Sheet with new data."""
    service = authenticate_google_sheets()
    if not service:
        print("❌ Error: Failed to authenticate Google Sheets API.")
        return
    
    next_row = find_next_empty_row(service, SPREADSHEET_ID, sheet_name)
    if not next_row:
        print("❌ Error: Could not determine the next empty row.")
        return
    
    try:
        range_name = f"{sheet_name}!A{next_row}"
        body = {"values": [[data]]}

        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name,
            valueInputOption="RAW",
            body=body
        ).execute()
        print("✅ Data successfully updated in Google Sheets.")
    
    except Exception as e:
        print(f"❌ Error updating Google Sheets: {e}")

def reset_google_sheets(sheet_name):
    """Clears all data in a given Google Sheets sheet."""
    service = authenticate_google_sheets()
    if not service:
        print("❌ Error: Failed to authenticate Google Sheets API.")
        return
    
    try:
        service.spreadsheets().values().clear(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_name}!A:Z"
        ).execute()
        print(f"✅ {sheet_name} has been cleared in Google Sheets.")
    
    except Exception as e:
        print(f"❌ Error resetting Google Sheets: {e}")
