import os
from multiprocessing import Pool
from glob import glob
from process_grib_cfsv2 import process_grib_file
import sys

def main():
    # Base directory
    base_dir = '/Volumes/Desk_SSD/ROMS/RE-FORECAST/GET-DATA/OCN/grb_file/'

    # Ask the user for the ending part of the local_dir (e.g., '2015/0201')
    user_input = sys.argv[1] 
    # Construct the final local_dir by appending the user-provided input
    local_dir = os.path.join(base_dir, user_input)
    
    # Ensure the directory exists
    if not os.path.isdir(local_dir):
        print(f"Directory {local_dir} does not exist. Exiting.")
        return
    
    print(f"Processing GRB files in: {local_dir}")

    # Create a list of processing tasks
    tasks = []

    # List all files that match the pattern 'ocnf*.grb2'
    file_list = glob(os.path.join(local_dir, 'ocnf*.grb2'))
    print(f"Found {len(file_list)} files in {local_dir}")

    # Process each GRB file
    for file_path in file_list:
        file_name = os.path.basename(file_path)

        # Extract date information from the filename (assuming the format 'ocnfYYYYMMDDHH*.grb2')
        date_str = file_name[4:14]  # Extract 'YYYYMMDDHH'
        year = int(date_str[:4])
        month = int(date_str[4:6])
        day = int(date_str[6:8])
        hour = int(date_str[8:10])
        
        download_dir = f'/Volumes/Desk_SSD/ROMS/RE-FORECAST/GET-DATA/OCN/nc_ocn/{user_input}'
        os.makedirs(download_dir, exist_ok=True)

        output_path = f"/Volumes/Desk_SSD/ROMS/RE-FORECAST/GET-DATA/OCN/nc_ocn/{user_input}/data_{year:04d}_{month:02d}_{day:02d}_{hour:02d}.nc"
        print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        print('Processing file:', file_name)

        # Check if the GRB file exists (it should, since it's listed)
        print('GRB exists:', file_path)

        if not os.path.exists(output_path):  # or os.path.getsize(output_path) <= 95 * 1024 * 1024:
            print('Processing NC:', file_path)
            tasks.append((file_path, output_path))
        else:
            print(f"NetCDF file {output_path} already exists. Skipping.")

    # Use multiprocessing to process files in parallel
    if tasks:
        with Pool(processes=4) as pool:
            pool.map(process_grib_file, tasks)
    else:
        print("No files to process.")

if __name__ == "__main__":
    main()

