#!/bin/bash

year=2013

for MONTH in $(seq -w 02 12); do
    echo "📦 Processing month: $MONTH/$year"

    # 🔹 Set target directory
    TARGET_DIR="/Volumes/Desk_SSD/ROMS/RE-FORECAST/GET-DATA/OCN/nc_ocn/${year}/${MONTH}01"

    # 🔍 Remove macOS metadata files (e.g., ._data_*.nc)
    echo "🧹 Cleaning up unwanted files in $TARGET_DIR..."
    find "$TARGET_DIR" -type f -name "._data_*.nc" -delete
    echo "📦 Running make_bdry_cfs.py for $MONTH/$year..."
    python3 make_bdry_cfs.py $year/${MONTH}01
done

