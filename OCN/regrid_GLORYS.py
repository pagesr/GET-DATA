import xarray as xr
import xesmf

def regrid_GLORYS(fld, method='nearest_s2d', irange=None, jrange=None):
    coords = xr.open_dataset('../ATM/NWGOA_grid_3.nc')
    coords = coords.rename({'lon_rho': 'lon', 'lat_rho': 'lat'})
    gsource = xr.open_dataset('grid/grid_forecast.nc')
    #gsource = gsource.rename({'longitude': 'lon', 'latitude': 'lat'})

    if irange is not None:
        gsource = gsource.isel(lon=slice(irange[0],irange[1]))

    if jrange is not None:
        gsource = gsource.isel(lat=slice(jrange[0],jrange[1]))

    regrid = xesmf.Regridder(
        gsource,
        coords,
        method=method,
        periodic=False,
        filename='regrid_cfd_roms.nc',
        reuse_weights=True
    )
    tdest = regrid(fld)
    return tdest
