#!/bin/bash

# 🚨 Set the year to clean
year=2013

# 📁 Base directory
BASE_DIR="/Volumes/Desk_SSD/ROMS/RE-FORECAST/GET-DATA/OCN/clm/$year"

# 📂 Month-day subfolders
FOLDERS=("0101" "0201" "0301" "0401" "0501" "0601" "0701" "0801" "0901" "1001" "1101" "1201")

echo "🧹 Cleaning .nc files for year: $year"

# 🔁 Loop through each folder
for FOLDER in "${FOLDERS[@]}"; do
    echo "📂 Folder: $FOLDER"

    # 🔹 Step 1: Remove all .nc files in the base/$FOLDER directory
    FOLDER_PATH="${BASE_DIR}/${FOLDER}"
    if [ -d "$FOLDER_PATH" ]; then
        echo "   - Removing *.nc in $FOLDER_PATH"
        rm -f "${FOLDER_PATH}"/*.nc
    fi

    # 🔹 Step 2: Remove CLM files in concat_monthly subdirectory
    CONCAT_DIR="${FOLDER_PATH}/concat_monthly"
    if [ -d "$CONCAT_DIR" ]; then
        echo "   - Removing CLM_CFS_${year}*.nc and CLM_CFS_${FOLDER}.nc in $CONCAT_DIR"
        rm -f "${CONCAT_DIR}/CLM_CFS_${year}"*.nc
        rm -f "${CONCAT_DIR}/CLM_CFS_${FOLDER}.nc"
    fi
done

echo "✅ Cleanup complete."

