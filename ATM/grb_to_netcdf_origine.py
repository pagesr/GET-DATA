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
from regridCFSV2_xesmf_to_roms import regrid_GLBy_JRA
from scipy.spatial import cKDTree
import subprocess
#######
# Get the needed ROMS stuff
roms_grid =Dataset('NWGOA_grid_3.nc','r')
rlat = roms_grid.variables['lat_rho'][:]
rlon = roms_grid.variables['lon_rho'][:]
mask_fill=roms_grid.variables['mask_rho'][:,0:326]
angle=roms_grid.variables['angle']
grid= Dataset('NWGOA_grid_3.nc')
bathy=grid['h']
########
def update_with_nearest_valid(t, mask_fill):
    """
    Update the `t` array by replacing NaN values with the nearest valid value based on `mask_fill`.

    Parameters:
    t (numpy.ndarray): The array to be updated. Shape should be (1, height, width).
    mask_fill (numpy.ndarray): The mask array indicating which NaNs should be replaced. Shape should be (height, width).
    """
    # Get the coordinates of valid (non-NaN) values
    valid_mask = ~np.isnan(t[:,:])
    valid_coords = np.column_stack(np.where(valid_mask))

    # Create a KDTree for quick nearest neighbor lookup
    tree = cKDTree(valid_coords)

    # Iterate over the t array and update NaN values
    for j in range(282):
        for i in range(326):
            if np.isnan(t[ j, i]) and mask_fill[j, i] == 1:
                # Find the nearest valid value
                dist, idx = tree.query([j, i])
                nearest_valid_coord = valid_coords[idx]
                nearest_valid_value = t[ nearest_valid_coord[0], nearest_valid_coord[1]]
                t[ j, i] = nearest_valid_value
    return t

########
from scipy.ndimage import distance_transform_edt

def update_land_sea_mask(mask_fill):
    """
    Update the land-sea mask to mark the first ocean cell grid as -1.

    Parameters:
    mask_fill (numpy.ndarray): The mask array with dimensions (282, 326) where 0 is land and 1 is ocean.

    Returns:
    numpy.ndarray: The updated mask array with the first ocean cells marked as -1.
    """
    # Identify the land (0) and ocean (1) cells
    land_mask = mask_fill == 0
    ocean_mask = mask_fill == 1

    # Calculate distance from each cell to the nearest land cell
    distance_to_land = distance_transform_edt(ocean_mask)

    # Get the coordinates of the first nearest ocean cells to the land
    first_ocean_coords = []
    for j in range(mask_fill.shape[0]):
        for i in range(mask_fill.shape[1]):
            if ocean_mask[j, i] and distance_to_land[j, i] == 1:
                first_ocean_coords.append((j, i))

    # Create a new mask with -1 for the first ocean cells
    updated_mask = mask_fill.copy()
    for coord in first_ocean_coords:
        updated_mask[coord] = -1

    return updated_mask
#############################
def rotate_uv(Uvar, Vvar, angle):
    # Rotate the UV assuming the angle is 0 on the native grid. 
    U = Uvar + Vvar * 1j
    eitheta = np.exp(-1j * angle[:])
    U = U * eitheta
    dst_u = np.real(U)
    dst_v = np.imag(U)
    return dst_u, dst_v
##########################
# Function to determine the number of days in a month, accounting for leap years
def days_in_month(year, month):
    if month == 2:  # February
        if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
            return 29  # Leap year
        else:
            return 28
    elif month in [4, 6, 9, 11]:
        return 30
    else:
        return 31



def process_grib_file(gribfile_path, datasets):
    """Process a single GRIB file and append its data to the datasets."""
    try:
        gribfile = pygrib.open(gribfile_path)
        print('grib path',gribfile_path)
        
# Extract '2015073006' from 'flxf2015073006.01.2015010100.grb2'
        date_str = os.path.basename(gribfile_path).split('.')[0][4:14]  
        date = np.datetime64(f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}T{date_str[8:10]}:00:00")
        # Extract date from the GRIB file (assuming the date is in the file name)

        print(date)
        
        # Calculate the time variable in days since 1900-01-01
        base_time = np.datetime64("1900-01-01T00:00:00")
        time_in_days = (date - base_time).astype('timedelta64[h]').astype(float) / 24.0
        print(time_in_days)
        # Extract land-sea mask
        lsm = gribfile.select(name='Land-sea mask')[0]
        lsm_data = lsm.values
        # land to -1
        lsm_data[lsm_data[:]==1]=-1
        lsm_data[lsm_data[:]==0]=1
        #land to 0
        lsm_data[lsm_data[:]==-1]=0
        updated_mask_fill = update_land_sea_mask(lsm_data)
        updated_mask_fill[updated_mask_fill[:]==-1]=0
        updated_mask_fill[updated_mask_fill[:]==0]=np.nan
        #lsm_data=1
        
        # Select the variables (has to be selected manually, could be better)
        u_wind = gribfile.select(name='10 metre U wind component')[0]
        v_wind = gribfile.select(name='10 metre V wind component')[0]
        specific_humidity = gribfile.select(name='Specific humidity')[0]
        # Try multiple names for short-wave radiation
        try:
            downward_sw_radiation = gribfile.select(name='Downward short-wave radiation flux')[0]
        except:
            downward_sw_radiation = gribfile.select(name='Surface downward short-wave radiation flux')[0]

        # Try multiple names for long-wave radiation
        try:
            downward_lw_flux = gribfile.select(name='Downward long-wave radiation flux')[0]
        except:
            downward_lw_flux = gribfile.select(name='Surface downward long-wave radiation flux')[0]
#        downward_sw_radiation = gribfile.select(name='Surface downward short-wave radiation flux')[0]
#        downward_lw_flux = gribfile.select(name='Surface downward long-wave radiation flux')[0]
        temperature = gribfile.select(name='Temperature')[0]
        precipitation = gribfile.select(name='Precipitation rate')[0]
        surface_pressure = gribfile.select(name='Surface pressure')[0]

        
                    
                    
        # Extract data, lats, and lons
        u_data, lats, lons = u_wind.data()
        u_data=u_data[:]*updated_mask_fill
        v_data = v_wind.values*updated_mask_fill
        sh_data = specific_humidity.values*updated_mask_fill
        dsr_data = downward_sw_radiation.values*updated_mask_fill
        dlf_data = downward_lw_flux.values #*lsm_data
        temp_data = temperature.values*updated_mask_fill
        precip_data = precipitation.values*updated_mask_fill
        sp_data = surface_pressure.values #*lsm_data
        method='nearest_s2d'
        # Interpolate on ROMS grid has to be : 'xxxx_time', 'eta_rho', 'xi_rho'
        # FOR V & U
        dst_varV = regrid_GLBy_JRA(v_data, method=method)
        dst_varU = regrid_GLBy_JRA(u_data, method=method)
        Ur, Vr = rotate_uv(dst_varU, dst_varV, angle)
        Ur = update_with_nearest_valid( np.array(Ur) , mask_fill)
        Ur[np.isnan(Ur[:])==True]=-32767.
        
        Vr = update_with_nearest_valid( np.array(Vr) , mask_fill)
        Vr[np.isnan(Vr[:])==True]=-32767.
        
        # For other variables
        Pair_int = regrid_GLBy_JRA(sp_data, method=method)
        
        #valid_mask = (~np.isnan(Pair_int[:, :])) & (np.array(bathy[:]) > 100) & (np.array(mask_fill[:]) == 1) 
        #valid_coords = np.column_stack(np.where(valid_mask))
        #mask_bathy=np.ones([282,326])*mask_fill
        #mask_bathy[valid_mask[:]==0]=np.nan
        Pair_int = update_with_nearest_valid( np.array(Pair_int) , mask_fill)
        Pair_int[np.isnan(Pair_int[:])==True]=-32767.
        
        Tair_int = regrid_GLBy_JRA(temp_data, method=method)
        #Tair_int[Tair_int[:]<263.15]=np.nan
        #Tair_int[Tair_int[:]>310]=np.nan
        Tair_int = update_with_nearest_valid( np.array(Tair_int) , mask_fill)
        Tair_int[np.isnan(Tair_int[:])==True]=-32767.
        
        Qair_int = regrid_GLBy_JRA(sh_data, method=method)
        Qair_int = update_with_nearest_valid( np.array(Qair_int) , mask_fill)
        Qair_int[np.isnan(Qair_int[:])==True]=-32767.
        
        rain_int = regrid_GLBy_JRA(precip_data, method=method)
        rain_int = update_with_nearest_valid( np.array(rain_int) , mask_fill)
        rain_int[np.isnan(rain_int[:])==True]=-32767.
        
        lwrad_down_int = regrid_GLBy_JRA(dlf_data, method=method)
        lwrad_down_int = update_with_nearest_valid( np.array(lwrad_down_int) , mask_fill)
        lwrad_down_int[np.isnan(lwrad_down_int[:])==True]=-32767.
        
        swrad_int = regrid_GLBy_JRA(dsr_data, method=method)
        swrad_int = update_with_nearest_valid( np.array(swrad_int) , mask_fill)
        swrad_int[np.isnan(swrad_int[:])==True]=-32767.
        
        #print(Tair_int)
        
        # Append data to datasets
        datasets['time'].append(time_in_days)
        datasets['Uwind'].append(Ur)
        datasets['Vwind'].append(Vr)
        datasets['Pair'].append(Pair_int)
        datasets['Tair'].append(Tair_int)
        datasets['Qair'].append(Qair_int)
        datasets['rain'].append(rain_int)
        datasets['lwrad_down'].append(lwrad_down_int)
        datasets['swrad'].append(swrad_int)
        
        print(f"Processed GRIB file: {gribfile_path}")
    except Exception as e:
        print(f"Failed to process kiki {gribfile_path}: {e}")

def create_monthly_ncfiles(datasets, out_dir, rlon_shape, year, month, day, hour):
    """Create NetCDF files for each variable and write the concatenated data."""
    variables = ['Uwind', 'Vwind','Pair','Tair', 'Qair', 'rain', 'lwrad_down', 'swrad']
    
    for var in variables:
        cfile = Dataset(os.path.join(out_dir, f'{var}_{year}_{month:02d}_{day:02d}_{hour:02d}.nc'), 'w', format='NETCDF4')
        cfile.createDimension('eta_rho', rlon_shape[0])
        cfile.createDimension('xi_rho', rlon_shape[1])
        
        if var in ['Uwind', 'Vwind']:
            time_dim = 'wind_time'
            cfile.createDimension(time_dim, len(datasets['time']))
            cfile.createVariable(time_dim, 'f8', (time_dim,))
            cfile.variables[time_dim].units = 'days since 1900-01-01 00:00:00'
            cfile.variables[time_dim].calendar = 'gregorian'
            cfile.variables[time_dim][:] = np.array(datasets['time'], dtype=float)

            cfile.createVariable(var, 'f8', (time_dim, 'eta_rho', 'xi_rho'),fill_value=-32767.)
            cfile.variables[var].long_name = f'{var} variable'
            cfile.variables[var].units = 'm s-1'  # Adjust as needed
            cfile.variables[var].wind_time = 'time'
            cfile.variables[var].missing_value = -32767. # Adjust as needed
            cfile.variables[var].field = f"{var}, scalar, series"
            cfile.variables[var][:] = np.array(datasets[var], dtype=float)
            cfile.close()
            print(f"Created NetCDF file: {var}_{year}_{month:02d}.nc")
            
        elif var in ['swrad']:
            time_dim = 'srf_time'
            cfile.createDimension(time_dim, len(datasets['time']))
            cfile.createVariable(time_dim, 'f8', (time_dim,))
            cfile.variables[time_dim].units = 'days since 1900-01-01 00:00:00'
            cfile.variables[time_dim].calendar = 'gregorian'
            cfile.variables[time_dim][:] = np.array(datasets['time'], dtype=float)
            
            cfile.createVariable(var, 'f8', (time_dim, 'eta_rho', 'xi_rho'),fill_value=-32767.)
            cfile.variables[var].long_name = f'{var} variable'
            cfile.variables[var].units = 'W m-2'  # Adjust as needed
            cfile.variables[var].srf_time = 'time'
            cfile.variables[var].missing_value = -32767. # Adjust as needed
            cfile.variables[var].field = f"{var}, scalar, series"
            cfile.variables[var][:] = np.array(datasets[var], dtype=float)
            cfile.close()
            print(f"Created NetCDF file: {var}_{year}_{month:02d}.nc")
        elif var in ['lwrad_down']:
            time_dim = 'lrf_time'
            cfile.createDimension(time_dim, len(datasets['time']))
            cfile.createVariable(time_dim, 'f8', (time_dim,))
            cfile.variables[time_dim].units = 'days since 1900-01-01 00:00:00'
            cfile.variables[time_dim].calendar = 'gregorian'
            cfile.variables[time_dim][:] = np.array(datasets['time'], dtype=float)
            
            cfile.createVariable(var, 'f8', (time_dim, 'eta_rho', 'xi_rho'))
            cfile.variables[var].long_name = f'{var} variable'
            cfile.variables[var].units = 'W m-2'  # Adjust as needed
            cfile.variables[var].lrf_time = 'time'
            cfile.variables[var].field = f"{var}, scalar, series"
            cfile.variables[var][:] = np.array(datasets[var], dtype=float)
            cfile.close()
        elif var in ['Pair']:
            time_dim = f'{var.lower()}_time'
            cfile.createDimension(time_dim, len(datasets['time']))
            cfile.createVariable(time_dim, 'f8', (time_dim,))
            cfile.variables[time_dim].units = 'days since 1900-01-01 00:00:00'
            cfile.variables[time_dim].calendar = 'gregorian'
            cfile.variables[time_dim][:] = np.array(datasets['time'], dtype=float)

            
            cfile.createVariable(var, 'f8', (time_dim, 'eta_rho', 'xi_rho'))
            cfile.variables[var].long_name = f'{var} variable'
            cfile.variables[var].units = 'Pa'  # Adjust as needed
            cfile.variables[var].pair_time = 'time'
            cfile.variables[var].field = f"{var}, scalar, series"
            cfile.variables[var][:] = np.array(datasets[var], dtype=float)
            cfile.close()
        elif var in ['Qair']:
            time_dim = f'{var.lower()}_time'
            cfile.createDimension(time_dim, len(datasets['time']))
            cfile.createVariable(time_dim, 'f8', (time_dim,))
            cfile.variables[time_dim].units = 'days since 1900-01-01 00:00:00'
            cfile.variables[time_dim].calendar = 'gregorian'
            cfile.variables[time_dim][:] = np.array(datasets['time'], dtype=float)

            
            cfile.createVariable(var, 'f8', (time_dim, 'eta_rho', 'xi_rho'))
            cfile.variables[var].long_name = f'{var} variable'
            cfile.variables[var].units = '1'  # Adjust as needed
            cfile.variables[var].qair_time = 'time'
            cfile.variables[var].field = f"{var}, scalar, series"
            cfile.variables[var][:] = np.array(datasets[var], dtype=float)
            cfile.close()   
                     
        elif var in ['Tair']:
            time_dim = f'{var.lower()}_time'
            cfile.createDimension(time_dim, len(datasets['time']))
            cfile.createVariable(time_dim, 'f8', (time_dim,))
            cfile.variables[time_dim].units = 'days since 1900-01-01 00:00:00'
            cfile.variables[time_dim].calendar = 'gregorian'
            cfile.variables[time_dim][:] = np.array(datasets['time'], dtype=float)

            
            cfile.createVariable(var, 'f8', (time_dim, 'eta_rho', 'xi_rho'))
            cfile.variables[var].long_name = f'{var} variable'
            cfile.variables[var].units = 'K'  # Adjust as needed
            cfile.variables[var].tair_time = 'time'
            cfile.variables[var].field = f"{var}, scalar, series"
            cfile.variables[var][:] = np.array(datasets[var], dtype=float)
            cfile.close()          
        elif var in ['rain']:
            time_dim = f'{var.lower()}_time'
            cfile.createDimension(time_dim, len(datasets['time']))
            cfile.createVariable(time_dim, 'f8', (time_dim,))
            cfile.variables[time_dim].units = 'days since 1900-01-01 00:00:00'
            cfile.variables[time_dim].calendar = 'gregorian'
            cfile.variables[time_dim][:] = np.array(datasets['time'], dtype=float)

            
            cfile.createVariable(var, 'f8', (time_dim, 'eta_rho', 'xi_rho'))
            cfile.variables[var].long_name = f'{var} variable'
            cfile.variables[var].units = 'kg m-2 s-1'  # Adjust as needed
            cfile.variables[var].rain_time = 'time'
            cfile.variables[var].field = f"{var}, scalar, series"
            cfile.variables[var][:] = np.array(datasets[var], dtype=float)
            cfile.close()   

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
for M in range(1,2):
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


