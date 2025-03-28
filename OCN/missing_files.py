"""
============================================
 PATCH MISSING NETCDF FILES FOR GOA FORCING
============================================

Author: Remi Pagès
Email: rpages@alaska.edu

This script scans a directory of 6-hourly NetCDF forecast files (named in the format:
`data_YYYY_MM_DD_HH.nc`) for missing files in the time sequence.

When a file is missing, it:
  - Copies the most recent available NetCDF file
  - Adjusts its internal time by +6 hours (0.25 days)
  - Creates a symbolic link from the corrected file in a `corrected/` subfolder

The script also logs all missing files and operations in `replaced.log`.

----------------------
Usage:
    python3 patch_missing_files.py 201601

Where `201601` corresponds to the subdirectory:
    /center1/OAINAK/rpages/CFS/PHYSICS/FORECAST/GET_OCN_CFSV2/nc_ocn_new_cfsv2/201601

Only `.nc` files are scanned.

Requirements:
    - Python 3
    - netCDF4
    - Files must follow the naming pattern exactly

"""

import os
import netCDF4 as nc
import shutil
from datetime import timedelta, datetime
import sys

# Log file for warnings and actions
log_file = "replaced.log"

# Start fresh by clearing the log file
with open(log_file, "w") as f:
    f.write("")

# Function to adjust the time in the NetCDF file by adding 6 hours
def adjust_time_in_netcdf(filename):
    try:
        with nc.Dataset(filename, 'r+') as dataset:
            time_data = dataset.variables['time'][:]
            new_time_data = time_data + 0.25  # 6 hours = 0.25 days
            dataset.variables['time'][:] = new_time_data
        print(f"Adjusted time for {filename}")
    except Exception as e:
        print(f"Failed to adjust time for {filename}: {e}")

# Function to extract datetime from a NetCDF filename
def extract_date(file_name):
    """
    Assumes filenames like: 'data_YYYY_MM_DD_HH.nc'
    Extracts and returns a datetime object.
    """
    parts = file_name.split('_')
    date_str = f"{parts[1]}-{parts[2]}-{parts[3]} {parts[4][:2]}"
    return datetime.strptime(date_str, "%Y-%m-%d %H")

# Function to compute number of days in a month (handles leap years)
def days_in_month(year, month):
    if month == 2:
        if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
            return 29
        return 28
    elif month in [4, 6, 9, 11]:
        return 30
    return 31

# Directory setup
user_input = sys.argv[1]  # expects a string like '201601'
base_dir = f"/center1/OAINAK/rpages/CFS/PHYSICS/FORECAST/GET_OCN_CFSV2/nc_ocn_new_cfsv2/{user_input}"
corrected_dir = f"{base_dir}/corrected"
os.makedirs(corrected_dir, exist_ok=True)

# Gather all existing NetCDF files in the directory
all_files = sorted([f for f in os.listdir(base_dir) if f.endswith('.nc')])
all_dates = [extract_date(f) for f in all_files]

# Identify the range of dates from available files
first_date = min(all_dates)
last_date = max(all_dates)

# Print the first and last available file names
first_file = all_files[all_dates.index(first_date)]
last_file = all_files[all_dates.index(last_date)]
print(f"First file: {first_file}")
print(f"Last file: {last_file}")

# Start from the first date and iterate in 6-hour steps
current_date = first_date
filename_old = None  # Tracks the most recent available file

while current_date <= last_date:
    year = current_date.year
    month = current_date.month
    day = current_date.day
    hour = current_date.strftime('%H')

    filename = f"data_{year}_{month:02d}_{day:02d}_{hour}.nc"
    full_path = os.path.join(base_dir, filename)
    corrected_path = os.path.join(corrected_dir, filename)

    if not os.path.exists(full_path):
        # Log missing file
        with open(log_file, "a") as f:
            f.write(f"Warning: Missing file {filename}\n")

        if filename_old:
            # Copy previous file as fallback
            src_file = os.path.join(base_dir, filename_old)
            shutil.copy(src_file, corrected_path)
            print(f"Copied {filename_old} to {filename}")

            # Adjust time to reflect correct forecast step
            adjust_time_in_netcdf(corrected_path)

            # Create symbolic link in place of the missing file
            if not os.path.exists(full_path) and not os.path.islink(full_path):
                os.symlink(corrected_path, full_path)
                print(f"Created symbolic link for {filename}")
            else:
                print(f"File or symbolic link {filename} already exists, skipping.")
        else:
            with open(log_file, "a") as f:
                f.write(f"Warning: No previous file to copy for {filename}\n")
    else:
        print(f"Found: {filename}")
        filename_old = filename  # Update to latest valid file

    # Move forward 6 hours
    current_date += timedelta(hours=6)
