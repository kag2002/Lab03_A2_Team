import urllib.request
import re
import json
import sys

# Reconfigure stdout to handle UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

url = "https://docs.google.com/spreadsheets/d/1cCxxFfLgthGe16BHKLU0VAfWwAwOxE1lFIZQk4f8DE8/edit"

print(f"Fetching spreadsheet metadata from {url}...")
try:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req) as res:
        html = res.read().decode("utf-8")
        
    print("Searching for sheet tabs in HTML metadata...")
    # Search for INITIAL_DATA or wiz_global_data or similar variables
    # Google Sheets stores sheet grid info inside a list of sheets, where each sheet has:
    # {"id": <gid>, "title": "<title>", ...} or similar structure
    # Let's inspect the matches for "sheetId" or "gid"
    matches = re.findall(r'\{\s*\"sheetId\"\s*:\s*(\d+)\s*,\s*\"title\"\s*:\s*\"([^\"]+)\"', html)
    if not matches:
        matches = re.findall(r'\{\s*\"id\"\s*:\s*(\d+)\s*,\s*\"title\"\s*:\s*\"([^\"]+)\"', html)
    if not matches:
        # Check standard javascript array matches
        # e.g., [gid, name, ...]
        matches = re.findall(r'\[\s*(\d+)\s*,\s*\"([^\"]+)\"\s*,\s*\d+\s*\]', html)
        
    # Another broad check: let's scan for any string containing a number and a sheet-like title
    # Like: {"1": "Reading", "2": "Listening", ...}
    # Let's search inside the script blocks for the exact sheet names mentioned by the user
    # "Candidate list" or "Điểm 4 kỹ năng" or "Listening", "Reading", "Speaking", "Writing"
    # Let's search for sheet list patterns:
    sheet_list_match = re.search(r'\"chunks\"\s*:\s*(\[.*?\])', html)
    if sheet_list_match:
        print("Found chunks array!")
        
    print(f"Discovered {len(matches)} sheet candidates:")
    seen = set()
    for gid, title in matches:
        if gid not in seen:
            print(f"Sheet Name: {title} | GID: {gid}")
            seen.add(gid)
            
    # Let's try downloading from typical sequential sheet GIDs or brute-forcing some GIDs if needed?
    # Actually, let's search inside the HTML for the strings "Listening", "Reading", "Speaking", "Writing", "Danh sách"
    print("\n--- Scanning HTML for specific Vietnamese sheet names / keywords ---")
    keywords = ["Listening", "Reading", "Speaking", "Writing", "Danh sách", "Thí sinh", "Điểm"]
    for kw in keywords:
        found = len(re.findall(kw, html))
        print(f"Keyword '{kw}' matches: {found}")
        
except Exception as e:
    print("Error:", e)
