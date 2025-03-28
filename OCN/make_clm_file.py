import matplotlib
matplotlib.use('Agg')

import subprocess
import os
import sys
import numpy as np
from multiprocessing import Pool

import pyroms
import pyroms_toolbox

from remap_clm import remap_clm
from remap_clm_uv import remap_clm_uv

path = sys.argv[1]

#data_dir = 'monthly_ocn/'
data_dir = f'/Volumes/Desk_SSD/ROMS/RE-FORECAST/GET-DATA/OCN/nc_ocn/{path}/monthly/'
print(data_dir)
dst_dir=f'./clm/{path}/'
if not os.path.exists(dst_dir):
    os.makedirs(dst_dir)

lst_file = []

#year = np.str(year)
lst = subprocess.getoutput('ls ' + data_dir + '*.nc')
#lst = subprocess.getoutput('ls ' + data_dir + 'monthly_avg_1993_03.nc')
lst = lst.split()
lst_file = lst_file + lst

print('Build CLM file from the following file list:')
print(lst_file)
print(' ')

irange = (0, 720)
jrange = (0, 181)

src_grd_file = 'grid/grid_forecast.nc'
src_grd = pyroms_toolbox.Grid_GLORYS.get_nc_Grid_GLORYS(src_grd_file, irange=irange, jrange=jrange)
dst_grd = pyroms.grid.get_ROMS_grid('NWGOA3')

for file in lst_file :
    dst_grd = pyroms.grid.get_ROMS_grid('NWGOA3')
    zeta = remap_clm(file, 'sshg', src_grd, dst_grd, dst_dir=dst_dir, irange=irange, jrange=jrange)
    dst_grd = pyroms.grid.get_ROMS_grid('NWGOA3', zeta=zeta)
    remap_clm(file, 'thetao', src_grd, dst_grd, dst_dir=dst_dir, irange=irange, jrange=jrange)
    remap_clm(file, 'so', src_grd, dst_grd, dst_dir=dst_dir, irange=irange, jrange=jrange)
    remap_clm_uv(file, src_grd, dst_grd, dst_dir=dst_dir, irange=irange, jrange=jrange)


