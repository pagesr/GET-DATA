import netCDF4 as nc

input_file = 'grid_forecast.nc'
output_file = 'grid_forecast_notime.nc'

# Open the input file
ds_in = nc.Dataset(input_file, 'r')

# Create the output file
ds_out = nc.Dataset(output_file, 'w', format='NETCDF4')

# Copy dimensions except 'time'
for name, dimension in ds_in.dimensions.items():
    if name != 'time':
        ds_out.createDimension(name, (len(dimension) if not dimension.isunlimited() else None))

# Copy variables except 'time' variable
for name, variable in ds_in.variables.items():
    if 'time' in variable.dimensions:
        dims = tuple(dim for dim in variable.dimensions if dim != 'time')
        var_out = ds_out.createVariable(name, variable.datatype, dims)
        var_out.setncatts({k: variable.getncattr(k) for k in variable.ncattrs()})
        var_out[:] = variable[0, ...]  # Index the time dimension
    elif name != 'time':
        var_out = ds_out.createVariable(name, variable.datatype, variable.dimensions)
        var_out.setncatts({k: variable.getncattr(k) for k in variable.ncattrs()})
        var_out[:] = variable[:]

# Copy global attributes
ds_out.setncatts({k: ds_in.getncattr(k) for k in ds_in.ncattrs()})

# Close the datasets
ds_in.close()
ds_out.close()

