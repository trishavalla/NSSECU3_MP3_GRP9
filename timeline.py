import pandas as pd
import os
import pytz
from datetime import datetime
import glob
# Function to convert timestamps to UTC


# Define file paths
# Define file paths
output_dir = r"C:\Users\karl_\Documents\NSSECU3\Output"
evtx_file = recmd_files = glob.glob(os.path.join(output_dir, "*_EvtxECmd_Output.csv"))

appcompat_file = r"C:\Users\karl_\Documents\NSSECU3\Output\appcompat_output.csv"
recmd_files = glob.glob(os.path.join(output_dir, "*_RECmd_Batch_BatchExample_Output.csv"))
output_file = r"C:\Users\karl_\Documents\NSSECU3\Output\timeline.csv"
if recmd_files:
    recmd_file = max(recmd_files, key=os.path.getctime)
else:
    print("[-] No RECmd file found in the directory.")
    recmd_file = None  # Handle the case where no file exists

if evtx_file:
    evtx_file = max(evtx_file, key=os.path.getctime)
else:
    print("[-] No evtx_file found in the directory.")
    evtx_file = None  # Handle the case where no file exists

# Load CSV files
evtx_df = pd.read_csv(evtx_file, usecols=["TimeCreated", "EventId", "Provider", "UserName", "ExecutableInfo"], low_memory=False)
evtx_df.rename(columns={"TimeCreated": "Timestamp"}, inplace=True)
evtx_df["Source"] = "EvtxECmd"

appcompat_df = pd.read_csv(appcompat_file, usecols=["LastModifiedTimeUTC", "Path", "Executed"], low_memory=False)
appcompat_df.rename(columns={"LastModifiedTimeUTC": "Timestamp"}, inplace=True)
appcompat_df["Source"] = "AppCompatCacheParser"

recmd_df = pd.read_csv(recmd_file, usecols=["LastWriteTimestamp", "Description", "KeyPath", "ValueData"], low_memory=False)
recmd_df.rename(columns={"LastWriteTimestamp": "Timestamp"}, inplace=True)
recmd_df["Source"] = "RECmd"

# Convert timestamps to UTC
def process_dataframe(df):
    df["Timestamp"] = df["Timestamp"].astype(str)
    return df.dropna(subset=["Timestamp"])  # Drop rows with invalid timestamps

evtx_df = process_dataframe(evtx_df)
appcompat_df = process_dataframe(appcompat_df)
recmd_df = process_dataframe(recmd_df)

# Combine data
merged_df = pd.concat([evtx_df, appcompat_df, recmd_df], ignore_index=True)

# Ensure all timestamps are timezone-aware UTC
merged_df["Timestamp"] = pd.to_datetime(merged_df["Timestamp"], utc=True, errors='coerce')

# Drop any remaining NaT values
merged_df = merged_df.dropna(subset=["Timestamp"])

# Sort by timestamp
merged_df = merged_df.sort_values(by="Timestamp")

# Save to CSV
merged_df.to_csv(output_file, index=False)

print(f"[+] Merged forensic timeline saved to {output_file}")
