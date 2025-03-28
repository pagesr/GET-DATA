import netCDF4 as nc
import sys
import os

# Check for correct usage
if len(sys.argv) != 3:
    print("Usage: python modify_netcdf.py <input_file> <output_file>")
    sys.exit(1)

input_file = sys.argv[1]
output_file = sys.argv[2]

# Check if input file exists
if not os.path.exists(input_file):
    print(f"Input file '{input_file}' does not exist.")
    sys.exit(1)

# Open the input NetCDF file
with nc.Dataset(input_file, 'r') as src:

    # Create the output NetCDF file
    with nc.Dataset(output_file, 'w', format='NETCDF4') as dst:

        # Copy global attributes
        dst.setncatts({attr: src.getncattr(attr) for attr in src.ncattrs()})

        # Rename dimensions 'longitude' to 'lon' and 'latitude' to 'lat'
        dimension_map = {'longitude': 'lon', 'latitude': 'lat'}

        # Copy dimensions, renaming as needed, and excluding 'time'
        for name, dimension in src.dimensions.items():
            if name == 'time':
                continue  # Skip 'time' dimension
            new_dim_name = dimension_map.get(name, name)
            dst.createDimension(
                new_dim_name, (len(dimension) if not dimension.isunlimited() else None))

        # Handle variables
        for name, variable in src.variables.items():

            # Skip variables 'so', 'uo', 'vo', and 'time'
            if name in ['so', 'uo', 'vo', 'time']:
                continue

            # Rename 'thetao' to 'pt'
            var_name = 'pt' if name == 'thetao' else name

            # Rename 'longitude' and 'latitude' variables to 'lon' and 'lat'
            var_name = 'lon' if var_name == 'longitude' else var_name
            var_name = 'lat' if var_name == 'latitude' else var_name

            # Remove 'time' dimension from variable dimensions
            var_dims = tuple(
                dimension_map.get(dim, dim) for dim in variable.dimensions if dim != 'time')

            # Create variable in destination dataset
            dst_var = dst.createVariable(var_name, variable.datatype, var_dims)

            # Copy variable attributes
            dst_var.setncatts({attr: variable.getncattr(attr) for attr in variable.ncattrs()})

            # Copy data, handling variables with 'time' dimension
            if 'time' in variable.dimensions:
                # Index 'time' dimension to remove it
                data = variable[0, ...]
            else:
                data = variable[:]

            dst_var[:] = data

        # Copy over any remaining variables (e.g., coordinates) without 'time' dimension
        for name, variable in src.variables.items():
            if name in dst.variables:
                continue
            if 'time' not in variable.dimensions and name not in ['so', 'uo', 'vo', 'thetao', 'time']:
                # Rename 'longitude' and 'latitude' variables to 'lon' and 'lat'
                var_name = 'lon' if name == 'longitude' else name
                var_name = 'lat' if var_name == 'latitude' else var_name

                # Adjust dimensions
                var_dims = tuple(dimension_map.get(dim, dim) for dim in variable.dimensions)

                # Create variable in destination dataset
                dst_var = dst.createVariable(var_name, variable.datatype, var_dims)

                # Copy variable attributes
                dst_var.setncatts({attr: variable.getncattr(attr) for attr in variable.ncattrs()})

                # Copy data
                dst_var[:] = variable[:]

    print(f"Modified NetCDF file has been saved as '{output_file}'.")

