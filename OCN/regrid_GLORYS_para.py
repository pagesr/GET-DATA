import xarray as xr
import xesmf
import tempfile
import os

def regrid_GLORYS(fld, method='nearest_s2d', irange=None, jrange=None):
    coords = xr.open_dataset('../ATM/NWGOA_grid_3.nc')
    coords = coords.rename({'lon_rho': 'lon', 'lat_rho': 'lat'})
    gsource = xr.open_dataset('grid/grid_forecast.nc')
    
    if irange is not None:
        gsource = gsource.isel(lon=slice(irange[0], irange[1]))

    if jrange is not None:
        gsource = gsource.isel(lat=slice(jrange[0], jrange[1]))

    # Generate a unique temporary file name for each process
    with tempfile.NamedTemporaryFile(suffix='.nc', delete=False) as tmpfile:
        weight_filename = tmpfile.name

    regrid = xesmf.Regridder(
        gsource,
        coords,
        method=method,
        periodic=False,
        filename=weight_filename,
        reuse_weights=False
    )
    tdest = regrid(fld)

    # Clean up temporary weight file
    try:
        os.remove(weight_filename)
    except OSError as e:
        print(f"Error deleting temporary file {weight_filename}: {e}")

    return tdest
