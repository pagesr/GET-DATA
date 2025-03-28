import xarray as xr
import xesmf

def regrid_GLBy_JRA(fld, method='nearest_s2d'):
    coords = xr.open_dataset('NWGOA_grid_3.nc')
    coords = coords.rename({'lon_rho': 'lon', 'lat_rho': 'lat'})
    gsource = xr.open_dataset('flxf2015022206.01.2015010100.grb2.nc',decode_times=False)
    

    regrid = xesmf.Regridder(
        gsource,
        coords,
        method=method,
        periodic=False,
        filename='regrid_CFSV2_t.nc',
        reuse_weights=True
    )
    tdest = regrid(fld)
    return tdest
