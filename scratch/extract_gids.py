import urllib.request
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

url = "https://docs.google.com/spreadsheets/d/1cCxxFfLgthGe16BHKLU0VAfWwAwOxE1lFIZQk4f8DE8/edit"

print("Fetching HTML...")
try:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as res:
        html = res.read().decode("utf-8")
        
    print("Searching for sheet names and their corresponding GIDs...")
    # Sheets list structure in Google Sheets usually looks like:
    # [1234567, "Sheet Name", 0] or [ "1234567", "Sheet Name" ]
    # Let's search for the sheet names and print surrounding context!
    sheet_names = ["Listening", "Reading", "Speaking", "Writing"]
    for name in sheet_names:
        print(f"\nScanning for sheet: '{name}'")
        # Find all occurrences of the sheet name in the HTML
        for m in re.finditer(name, html):
            start = max(0, m.start() - 150)
            end = min(len(html), m.end() + 150)
            context = html[start:end]
            # Search for numbers of length 5-10 inside this context (which represents GID)
            gids = re.findall(r'\b(\d{7,10})\b', context)
            print(f"Match context around index {m.start()}:")
            print(f"  {repr(context)}")
            if gids:
                print(f"  Extracted potential GIDs: {gids}")
                
except Exception as e:
    print("Error:", e)
