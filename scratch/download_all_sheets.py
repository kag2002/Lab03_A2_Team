import urllib.request
import os
import sys

# Reconfigure stdout to handle UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# The 4 sheets extracted GIDs
sheets = {
    "Reading": "924156453",
    "Listening": "698342718",
    "Speaking": "72917778",
    "Writing": "1307923965"
}

output_dir = "c:\\Users\\Admin\\Documents\\VinUni\\CodeLab\\Day3\\C2-App-023\\data"
os.makedirs(output_dir, exist_ok=True)

print("Starting download of the 4 Toeic Skill sheets...")

for name, gid in sheets.items():
    csv_url = f"https://docs.google.com/spreadsheets/d/1cCxxFfLgthGe16BHKLU0VAfWwAwOxE1lFIZQk4f8DE8/export?format=csv&gid={gid}"
    target_path = os.path.join(output_dir, f"{name.strip().lower()}.csv")
    
    print(f"\n--- Downloading Sheet: {name} (GID: {gid}) ---")
    try:
        req = urllib.request.Request(
            csv_url,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req) as res:
            data = res.read().decode("utf-8")
            
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(data)
            
        lines = data.split("\n")
        print(f"Saved successfully to: {target_path}")
        print(f"Total candidate rows parsed: {len(lines) - 1}")
        print("Header and first candidate row:")
        if len(lines) >= 2:
            print(f"  Header: {lines[0].strip()}")
            print(f"  Row 1 : {lines[1].strip()}")
    except Exception as e:
        print(f"Failed to download sheet '{name}': {e}")
