import os
import sys
import dask
import dask.bag as db
import pyroms
import pyroms_toolbox
from remap_bdry import remap_bdry
from remap_bdry_uv import remap_bdry_uv
import subprocess

def file_exists_and_large_enough(file_path, min_size_mb=10):
    """Check if the file exists and is larger than the specified size in MB."""
    return os.path.exists(file_path) and os.path.getsize(file_path) > min_size_mb * 1024 * 1024

def process_file(file, src_grd_file):
    """Process a single file to create boundary files and merge them."""
    dst_dir = f'./bdry/{path}/'
    dst_grd = pyroms.grid.get_ROMS_grid('NWGOA3')
    bdry_file = os.path.join(dst_dir, file.rsplit('/')[-1][:-3] + '_bdry_' + dst_grd.name + '.nc')

    if file_exists_and_large_enough(bdry_file):
        print(f"File {bdry_file} already exists and is larger than 10MB. Skipping.")
        return

    irange = (0, 720)
    jrange = (0, 181)
    src_grd = pyroms_toolbox.Grid_GLORYS.get_nc_Grid_GLORYS(src_grd_file, irange=irange, jrange=jrange)
    zeta = remap_bdry(file, 'sshg', src_grd, dst_grd, dst_dir=dst_dir, irange=irange, jrange=jrange)
    dst_grd2 = pyroms.grid.get_ROMS_grid('NWGOA3', zeta=zeta)
    remap_bdry(file, 'thetao', src_grd, dst_grd, dst_dir=dst_dir, irange=irange, jrange=jrange)
    remap_bdry(file, 'so', src_grd, dst_grd2, dst_dir=dst_dir, irange=irange, jrange=jrange)
    remap_bdry_uv(file, src_grd, dst_grd2, dst_dir=dst_dir, irange=irange, jrange=jrange)

    merge_files(dst_dir, file, dst_grd)


def merge_files(dst_dir, file, dst_grd):
    """Merge the boundary files into a single NetCDF file."""
    variables = ['sshg', 'thetao', 'so', 'u', 'v']
    bdry_file = os.path.join(dst_dir, file.rsplit('/')[-1][:-3] + '_bdry_' + dst_grd.name + '.nc')

    try:
        # Create initial boundary file with sshg
        out_file = os.path.join(dst_dir, file.rsplit('/')[-1][:-3] + f'_{variables[0]}_bdry_' + dst_grd.name + '.nc')
        command = ['ncks', '-a', '-O', out_file, bdry_file]
        subprocess.check_call(command)
        os.remove(out_file)

        # Append remaining variables
        for var in variables[1:]:
            out_file = os.path.join(dst_dir, file.rsplit('/')[-1][:-3] + f'_{var}_bdry_' + dst_grd.name + '.nc')
            command = ['ncks', '-a', '-A', out_file, bdry_file]
            subprocess.check_call(command)
            os.remove(out_file)
    except subprocess.CalledProcessError as e:
        print(f"Error during subprocess call: {e}")
        print(f"Command: {command}")
        print(f"File: {file}")

# Main script
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 make_bdry_cfs.py <year>")
        sys.exit(1)

    #year = sys.argv[1]  # Get the year from the command-line arguments
    path = sys.argv[1]  # Get the year from the command-line arguments
    print(f"Processing data for year: {path}")

    data_dir = f'/Volumes/Desk_SSD/ROMS/RE-FORECAST/GET-DATA/OCN/nc_ocn/{path}'
    dst_dir = f'./bdry/{path}'
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
        print(f"Created directory: {dst_dir}")


    src_grd_file = 'grid/grid_forecast.nc'
    
    # Gather all files to process
    lst_file = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith('.nc')]
    
    # Convert the list to a Dask bag
    bag = db.from_sequence(lst_file, npartitions=8)
    
    # Process the files in parallel
    bag.map(lambda file: process_file(file, src_grd_file)).compute()

    print(f"All files for year {path} processed and merged successfully.")
