import subprocess
import os
import time
import csv
from datetime import datetime


# SET THIS PATH TO THE DIRECTORY WHERE YOU HAVE EXTRACTED THE TOOLS
EVTXECMD_PATH = r"C:\zimmertools\net6\EvtxeCmd\EvtxECmd.exe"
RECMD_PATH = r"C:\zimmertools\net6\RECmd\RECmd.exe"
APPCOMPATCACHEPARSER_PATH = r"C:\zimmertools\net6\AppCompatCacheParser.exe"

# SET THESE PATHS TO THE DIRECTORIES WHERE YOUR INPUT FILES ARE LOCATED
EVTX_INPUT_DIR = r"C:\Users\karl_\Documents\NSSECU3\evtxINPUT"
REGISTRY_INPUT_DIR = r"C:\Users\karl_\Documents\NSSECU3\registryHivesINPUT"
OUTPUT_DIR = r"C:\Users\karl_\Documents\NSSECU3\Output"
SYSTEM_FILE_PATH = os.path.join(REGISTRY_INPUT_DIR, "SYSTEM")

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Define output files
EVTX_OUTPUT = os.path.join(OUTPUT_DIR, "evtx_output.txt")
RECMD_OUTPUT = os.path.join(OUTPUT_DIR, "recmd_output.txt")
APPCOMPAT_CSV = os.path.join(OUTPUT_DIR, "appcompat_output.csv")
FINAL_CSV_OUTPUT = os.path.join(OUTPUT_DIR, "forensic_output.csv")
TIMELINE_CSV_OUTPUT = os.path.join(OUTPUT_DIR, "timeline_output.csv")  # For Timeline Explorer output

# Function to run a command with error handling
def run_command(command, output_file):
    """Runs a subprocess command and writes output to a file."""
    try:
        with open(output_file, "w") as f:
            subprocess.run(command, stdout=f, stderr=f, text=True, check=True)
        print(f"[+] Successfully executed: {' '.join(command)}")
    except subprocess.CalledProcessError as e:
        print(f"[!] Error executing {' '.join(command)}: {e}")

# Function to execute EvtxECmd
def run_evtxecmd():
    if os.path.exists(EVTXECMD_PATH):
        cmd = [EVTXECMD_PATH, "-d", EVTX_INPUT_DIR, "--csv", OUTPUT_DIR]
        run_command(cmd, EVTX_OUTPUT)
    else:
        print(f"[!] EvtxECmd.exe not found at {EVTXECMD_PATH}")

# Function to execute RECmd
def run_recmd():
    if os.path.exists(RECMD_PATH):
        RULE_FILE = r"C:\zimmertools\net6\RECmd\BatchExamples\BatchExample.reb"
        cmd = [RECMD_PATH, "-d", REGISTRY_INPUT_DIR, "--csv", OUTPUT_DIR, "--bn", RULE_FILE]
        run_command(cmd, RECMD_OUTPUT)
    else:
        print(f"[!] RECmd.exe not found at {RECMD_PATH}")

# Function to execute AppCompatCacheParser
def run_appcompatcacheparser():
    if os.path.exists(APPCOMPATCACHEPARSER_PATH):
        cmd = [APPCOMPATCACHEPARSER_PATH, "-f", SYSTEM_FILE_PATH, "--csv", OUTPUT_DIR, "--csvf", "appcompat_output.csv"]
        print("[+] Running AppCompatCacheParser...")
        process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Wait for the process to complete
        process.wait()

        # Wait until the output file exists
        while not os.path.exists(APPCOMPAT_CSV):
            print("[!] Waiting for AppCompatCacheParser output file to be created...")
            time.sleep(1)

        # Ensure the file is not still being written to
        while True:
            try:
                with open(APPCOMPAT_CSV, "r") as f:
                    f.read()
                break  # If we can read it, it's ready
            except PermissionError:
                print("[!] File is still in use, waiting...")
                time.sleep(1)

        print(f"[+] Successfully processed AppCompatCacheParser output: {APPCOMPAT_CSV}")
    else:
        print(f"[!] AppCompatCacheParser.exe not found at {APPCOMPATCACHEPARSER_PATH}")

# Run the tools
print("[+] Running EvtxECmd...")
run_evtxecmd()
print("[+] Running RECmd...")
run_recmd()
print("[+] Running AppCompatCacheParser...")
run_appcompatcacheparser()

# Function to normalize timestamp to UTC
def normalize_timestamp(timestamp_str, source):
    """Normalizes timestamp to UTC+0 (ISO 8601 format)."""
    try:
        # Assuming the timestamp is in the format 'YYYY-MM-DD HH:MM:SS' or similar
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        return timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")  # ISO 8601 format (UTC)
    except Exception as e:
        print(f"[!] Error normalizing timestamp for {source}: {e}")
        return timestamp_str  # Return original timestamp if it cannot be normalized

# Merge and structure the CSV files
def merge_csv_files_for_timeline():
    """Merge forensic tool outputs into a structured CSV file for a Timeline Explorer."""
    with open(TIMELINE_CSV_OUTPUT, "w", encoding="utf-8", newline="") as f_out:
        writer = csv.writer(f_out)

        # Write the header for Timeline Explorer format
        writer.writerow(["Timestamp (UTC+0)", "Artifact", "Event Description", "Tool", "Additional Info"])

        data_files = {
            "EvtxECmd": EVTX_OUTPUT,
            "RECmd": RECMD_OUTPUT,
            "AppCompatCacheParser": APPCOMPAT_CSV
        }

        for source, file_path in data_files.items():
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f_in:
                    reader = csv.reader(f_in)
                    headers = next(reader, None)  # Skip the header if exists
                    
                    for row in reader:
                        if row:  # If there is data in the row
                            print(f"Row data from {source}: {row}")

                            # Handle EvtxECmd: Check if the row contains a valid timestamp
                            if source == "EvtxECmd" and len(row) >= 1 and 'Author' not in row[0]:
                                # Assuming timestamp is in the first column
                                timestamp = row[0]
                                normalized_timestamp = normalize_timestamp(timestamp, source)
                                
                                # Assuming event description is in the second column (adjust if needed)
                                event_description = row[1] if len(row) > 1 else "No description"
                                additional_info = row[2] if len(row) > 2 else "No additional info"
                                
                                # Write each event to the timeline output
                                writer.writerow([normalized_timestamp, source, event_description, source, additional_info])
                                print(f"[+] Processed row: {row}")
                            elif source == "AppCompatCacheParser" and len(row) >= 4:
                                # Handle AppCompatCacheParser (timestamp is in 4th column)
                                timestamp = row[3]
                                normalized_timestamp = normalize_timestamp(timestamp, source)

                                # Assuming event description is in the third column (adjust if needed)
                                event_description = row[2]
                                additional_info = row[5]  # Modify as needed for more detailed info
                                
                                # Write each event to the timeline output
                                writer.writerow([normalized_timestamp, source, event_description, source, additional_info])
                                print(f"[+] Processed row: {row}")
                            else:
                                print(f"[!] Skipping invalid or incomplete row from {source}: {row}")
            else:
                print(f"[!] Warning: {source} output file not found ({file_path})")

    print(f"[+] Timeline-compatible CSV saved to: {TIMELINE_CSV_OUTPUT}")




# Call the function to create timeline-compatible CSV
merge_csv_files_for_timeline()
subprocess.run(["python", "timeline.py"])
print("creating timeline")
