#!/bin/bash

# 📆 Define the year
YEAR=2013

# 📁 Base directory (uses $YEAR)
BASE_DIR="/Volumes/Desk_SSD/ROMS/RE-FORECAST/GET-DATA/OCN/bdry/${YEAR}"

# 📁 Month-day subfolders
FOLDERS=("0201")
#FOLDERS=("0201" "0301" "0401" "0501" "0601" "0701" "0801" "0901" "1001" "1101" "1201")

# 🔁 Loop through each month folder
for FOLDER in "${FOLDERS[@]}"; do
    echo "📂 Processing folder: $FOLDER"

    # 📁 Full path to current folder
    FOLDER_PATH="${BASE_DIR}/${FOLDER}"

    # 📍 Output dir inside the folder
    OUTPUT_DIR="${FOLDER_PATH}/concat"
    mkdir -p "$OUTPUT_DIR"

    # 📆 Extract month
    MONTH=${FOLDER:0:2}

    # 🧾 Output filename
    OUTPUT_FILE="${OUTPUT_DIR}/CFS_BDRY_${YEAR}_${MONTH}.nc"

    # 🛑 Skip if exists
    if [ -f "$OUTPUT_FILE" ]; then
        echo "⚠️  File already exists: $OUTPUT_FILE. Skipping..."
        continue
    fi

    # 📦 Input files pattern
    INPUT_FILES="${FOLDER_PATH}/data_*_bdry_NWGOA3.nc"

    # 🔗 Concatenate if files are found
    if ls $INPUT_FILES 1> /dev/null 2>&1; then
        echo "🔗 Concatenating files in $FOLDER_PATH..."
        cdo cat $INPUT_FILES "$OUTPUT_FILE"
        echo "✅ Saved: $OUTPUT_FILE"
    else
        echo "❌ No matching files found in $FOLDER_PATH. Skipping..."
    fi
done

echo "🎉 All folders processed!"

