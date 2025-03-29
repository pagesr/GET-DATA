# Gulf of Alaska Forecast System (GOA-FS) Data Scripts

> **⚠️ This repository is under development.**

This repository contains scripts for downloading and processing oceanographic and atmospheric data for the **Gulf of Alaska Forecast System (GOA-FS)**.

> This version is tailored to download **historical forecasts**, specifically for the **first day of every month at 00:00**.

---

## ✉️ Overview

The repository is separated into two main components:

- **ATM**: Atmospheric forcing
- **OCN**: Oceanic boundary and climatology files

---

## 📂 Required Libraries

- `pygrib`
- `xesmf`
- `dask`
- `pyroms`
- `pyroms_toolbox`

> ⚡ For `pyroms`, see : [https://github.com/ESMG/pyroms](https://github.com/ESMG/pyroms)

---

## 🗋 Required Files

- ROMS grid file, e.g.: `NWGOA_grid_3.nc`

---

## 🌊 OCN Workflow

This part generates the **boundary** and **climatology** files required by ROMS (T, S, U, V, SSH).

### ✅ Part A: GRB to NetCDF

1. **Download GRB files**

   - Script: `dl_grb_ocn.py`
   - Failures are logged to `download_failures.log`
   - Failures may occur due to download bugs or missing data (which can be expected for some timestamps)

2. **Convert to NetCDF**

   - Script: `convert_grb.sh`
   - This calls: `grb_2_netcdf.py YEAR/MONTH`
   - Produces global ocean NetCDF files

3. **Handle Missing Files**

   - Script: `missing.sh`
   - Calls: `missing_files.py`
   - Automatically fills missing files using nearest-in-time replacement, adjusting timestamps
   - Outputs a log: `replaced.log` in `logs/`

4. **Compute Monthly Averages (Climatology)**

   - Script: `compute_monthly.sh`
   - Produces monthly climatology files for T, S, U, V, SSH

---

## 🚧 Part B: ROMS Forcing File Generation

### ① Boundary Files

- Script: `do_bdry.sh`
  - Calls `make_bdry_cfs.py` ➔ `remap_bdry.py`, `remap_bdry_uv.py`, and `regrid_GLORYS_para.py`
  - These perform regridding and interpolation onto ROMS grid
- Script: `concat_bdry.sh`
  - Concatenates the per-month boundary NetCDF files

### ② Climatology Files

- Script: `do_clm.sh`
  - Calls `make_clm_file.py`
    - Internally calls `remap_clm.py`, `remap_clm_uv.py` ➔ which both call `regrid_GLORYS.py`
- Script: `concat_clm.sh`
  - Concatenates monthly climatology files
- Script: `change_time.sh`
  - (Optional) Forces the time to start at 00:00 for consistency across files

---

For any issue or feedback, contact:
**Remi Pages**\
[rpages@alaska.edu](mailto\:rpages@alaska.edu)


