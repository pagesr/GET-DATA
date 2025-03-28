⚠️ **WARNING: This project is under active development and not yet finalized. Use with caution.**

# GET-DATA

This repository contains scripts for downloading and processing oceanographic data for the **Gulf of Alaska Forecast System (GOA-FS)**.

## Overview

The system is designed to:

- 📥 **Download** GRIB-format forecast data (e.g., from global models or reforecasts)
- 🧮 **Process** those files into NetCDF format
- ⚙️ **Regrid/interpolate** ocean variables (like temperature, salinity, currents) to the GOA ROMS grid
- 📦 Save clean, compressed NetCDF files for model forcing or analysis

## Folder Contents

- `*.py`: Python scripts for GRIB parsing, variable extraction, NetCDF creation
- `*.sh`: Shell scripts for automation (e.g., file download or batch processing)
- `grb_file/`: Folder where raw `.grb2` files are stored (ignored by Git)
- `out_clean_flx_cfsv2/` or similar: Folder for processed NetCDF output

## Variables Handled

- Sea Surface Height
- 3D Potential Temperature
- 3D Salinity
- 3D Ocean Currents (U and V components)

## How to Use

1. Place your GRIB files into the `grb_file/` directory
2. Run the appropriate Python or shell script
3. NetCDF output will be saved in the configured `out_*` folder

## Git Info

Only `.py` and `.sh` files are tracked in Git. All other data/output is excluded using `.gitignore`.

---

## Author

**Remi Pagès**  
Email: [rpages@alaska.edu](mailto:rpages@alaska.edu)

