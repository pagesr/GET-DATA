import os
import numpy as np
import pygrib
from netCDF4 import Dataset

def process_grib_file(file_info):
    """Process the GRIB file to extract variables and save them in NetCDF format with compression."""
    file_path, output_path = file_info
    try:
        # Extract date
        date_str = os.path.basename(file_path).split('.')[0][4:14]  # Extract "YYYYMMDDHH"
        date = np.datetime64(f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}T{date_str[8:10]}:00:00")
        print(f"Extracted date: {date}")

        base_time = np.datetime64("1900-01-01T00:00:00")
        time_in_days = (date - base_time).astype('timedelta64[h]').astype(float) / 24.0
        print(f"Time in days since 1900-01-01: {time_in_days}")

        grbs = pygrib.open(file_path)

        # Extract SSHG
        sshg_data, lats, lons = None, None, None
        try:
            for grb in grbs.select(name='Sea Surface Height Relative to Geoid'):
                sshg_data, lats, lons = grb.data()
                break
        except ValueError:
            pass

        # --- Variable Extraction Helper ---
        def extract_3d_variable(grbs, name=None, parameter_name=None, type_of_level="depthBelowSea"):
            data = []
            depths = []

            # Try name selector
            if name is not None:
                try:
                    messages = grbs.select(name=name)
                except ValueError:
                    messages = []

            if not messages and parameter_name is not None:
                try:
                    messages = grbs.select(parameterName=parameter_name, typeOfLevel=type_of_level)
                except ValueError:
                    return None, None

            if not messages:
                return None, None

            for grb in messages:
                depth = grb.level
                var_data, _, _ = grb.data()
                data.append(var_data)
                depths.append(depth)

            data = np.array(data[::-1])
            depths = np.array(depths[::-1])
            return data, depths

        # Extract 3D fields
        temperature_data, temp_depths = extract_3d_variable(grbs, name="Potential temperature")
        salinity_data, sal_depths = extract_3d_variable(grbs, name="Salinity")
        uo_data, uo_depths = extract_3d_variable(grbs, name="Eastward sea water velocity", parameter_name="u-component of current")
        vo_data, vo_depths = extract_3d_variable(grbs, name="Northward sea water velocity", parameter_name="v-component of current")

        # Check required fields
        if sshg_data is None:
            raise ValueError("Missing 'Sea Surface Height Relative to Geoid'")
        if any(x is None for x in [temperature_data, salinity_data, uo_data, vo_data]):
            raise ValueError("Missing temperature, salinity, or current fields")

        # Reformat coordinates
        lats = lats[:, 0]
        lons = lons[0, :]

        # Process data: convert units, set fill values
        temperature_data = temperature_data - 273.15
        temperature_data[temperature_data > 1200] = -32767
        salinity_data = salinity_data * 1000
        salinity_data[salinity_data > 100] = -32767
        uo_data[uo_data > 100] = -32767
        vo_data[vo_data > 100] = -32767

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Write to NetCDF
        ncfile = Dataset(output_path, 'w', format='NETCDF4')

        ncfile.createDimension('time', None)
        ncfile.createDimension('depth', len(temp_depths))
        ncfile.createDimension('latitude', len(lats))
        ncfile.createDimension('longitude', len(lons))

        comp = {'zlib': True, 'complevel': 4}

        time_var = ncfile.createVariable('time', 'f8', ('time',), **comp)
        depth_var = ncfile.createVariable('depth', 'f8', ('depth',), **comp)
        lat_var = ncfile.createVariable('latitude', 'f8', ('latitude',), **comp)
        lon_var = ncfile.createVariable('longitude', 'f8', ('longitude',), **comp)
        sshg = ncfile.createVariable('sshg', 'f8', ('time', 'latitude', 'longitude'), fill_value=-32767, **comp)
        thetao = ncfile.createVariable('thetao', 'f8', ('time', 'depth', 'latitude', 'longitude'), fill_value=-32767, **comp)
        so = ncfile.createVariable('so', 'f8', ('time', 'depth', 'latitude', 'longitude'), fill_value=-32767, **comp)
        uo = ncfile.createVariable('uo', 'f8', ('time', 'depth', 'latitude', 'longitude'), fill_value=-32767, **comp)
        vo = ncfile.createVariable('vo', 'f8', ('time', 'depth', 'latitude', 'longitude'), fill_value=-32767, **comp)

        # Metadata
        time_var.units = "days since 1900-01-01 00:00:00"
        time_var.calendar = "gregorian"
        depth_var.units = "m"
        depth_var.positive = "down"
        lat_var.units = "degrees_north"
        lon_var.units = "degrees_east"
        sshg.long_name = "Sea Surface Height Relative to Geoid"
        sshg.units = "m"
        thetao.long_name = "Potential Temperature"
        thetao.units = "Celsius"
        so.long_name = "Salinity"
        so.units = "PSU"
        uo.long_name = "Eastward Sea Water Velocity"
        uo.units = "m/s"
        vo.long_name = "Northward Sea Water Velocity"
        vo.units = "m/s"

        # Data writing
        time_var[:] = [time_in_days]
        depth_var[:] = temp_depths
        lat_var[:] = lats
        lon_var[:] = lons
        sshg[0, :, :] = sshg_data
        thetao[0, :, :, :] = temperature_data
        so[0, :, :, :] = salinity_data
        uo[0, :, :, :] = uo_data
        vo[0, :, :, :] = vo_data

        ncfile.close()
        print(f"✅ NetCDF file created: {output_path}")

    except Exception as e:
        print(f"❌ Failed to process {file_path}: {e}")
        with open("bug.txt", "a") as log:
            log.write(f"{file_path} — {e}\n")

