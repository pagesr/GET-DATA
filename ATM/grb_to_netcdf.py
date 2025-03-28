import numpy as np
from glob import glob
import sys
from netCDF4 import Dataset
import warnings
warnings.filterwarnings('ignore')
import numpy as np
import xarray as xr
import pygrib
import os
import requests
from tqdm import tqdm

import numpy as np
from netCDF4 import Dataset, date2num, num2date
from datetime import datetime, timedelta
####
#from regridCFSV2_xesmf_to_roms import regrid_GLBy_JRA
from scipy.spatial import cKDTree
import subprocess
#######
from grb_utils import process_grib_file, create_monthly_ncfiles, update_with_nearest_valid, update_land_sea_mask, rotate_uv, days_in_month 
# Get the needed ROMS stuff
roms_grid =Dataset('NWGOA_grid_3.nc','r')
rlat = roms_grid.variables['lat_rho'][:]
rlon = roms_grid.variables['lon_rho'][:]
mask_fill=roms_grid.variables['mask_rho'][:,0:326]
angle=roms_grid.variables['angle']
grid= Dataset('NWGOA_grid_3.nc')
bathy=grid['h']
########

# Initialize datasets
datasets = {
    'time': [],
    'Uwind': [],
    'Vwind': [],
    'Pair': [],
    'Tair': [],
    'Qair': [],
    'rain': [],
    'lwrad_down': [],
    'swrad': []
}




# Minimum file size to skip processing (600 KB in bytes)
min_file_size = 600 * 1024  # 600 KB
# Variables (names of NetCDF files)
variables = ['Uwind', 'Vwind', 'Pair', 'Tair', 'Qair', 'rain', 'lwrad_down', 'swrad']

Y='2013'

# Loop through the years, months, and days of 1993
for M in range(2,13):
    out_dir = f'./out_clean_flx_cfsv2/{Y}/{M:02d}01'
    os.makedirs(out_dir, exist_ok=True)
    print(f"out directory: {out_dir}")
    grib_dir = f'./grb_file/{Y}/{M:02d}01/'

    # List all files that match the pattern 'ocnf*.grb2'
    file_list = glob(os.path.join(grib_dir, 'flxf*.grb2'))
    print(f"Found {len(file_list)} files in {grib_dir}")
    # Process each GRB file
    for file_path in file_list:
        file_name = os.path.basename(file_path)
        #print('file_name ',file_name)
        date_str = file_name[4:14]  # Extract 'YYYYMMDDHH' from 'flxf2015073006'
        year = int(date_str[:4])     # Extract '2015'
        month = int(date_str[4:6])   # Extract '07'
        day = int(date_str[6:8])     # Extract '30'
        hour = int(date_str[8:10])   # Extract '06'
        #print(year,month,day,hour)

        local_file = os.path.join(grib_dir, file_name)

        # Check for the presence and size of NetCDF files for each variable
        skip_processing = False
        for var in variables:
            output_file = os.path.join(out_dir, f'{var}_{year}_{month:02d}_{day:02d}_{hour:02d}.nc')
            # If the file exists and is larger than 600 KB, skip processing
            if os.path.exists(output_file) and os.path.getsize(output_file) > min_file_size:
                print(f"Skipping {output_file} (already exists and is larger than 600 KB)")
                skip_processing = True
                break

        if skip_processing:
            continue

        if os.path.exists(local_file):
            # Process the file
            print(f"Processing {local_file}")
            process_grib_file(local_file, datasets)

            # Create the NetCDF files for the processed GRIB data
            create_monthly_ncfiles(datasets, out_dir, rlon.shape, year, month, day, hour)

            # Reset datasets for the next set of files
            datasets = {
                'time': [],
                'Uwind': [],
                'Vwind': [],
                'Pair': [],
                'Tair': [],
                'Qair': [],
                'rain': [],
                'lwrad_down': [],
                'swrad': []
            }
    # CONCAT 
    for var in variables:
        concat_file=f'{var}_{Y}_{M:02d}01.nc'
        command = f"cdo cat {out_dir}/{var}*.nc {out_dir}/{concat_file}"
        subprocess.run(command, shell=True, check=True)

    subprocess.run(f'rm {out_dir}/*_*_*_*_*.nc', shell=True, check=True)


