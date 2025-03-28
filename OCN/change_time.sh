#!/bin/bash

YEAR=2013
BASE_DIR="/Volumes/Desk_SSD/ROMS/RE-FORECAST/GET-DATA/OCN/clm/${YEAR}"
FOLDERS=("0101" "0201" "0301" "0401" "0501" "0601" "0701" "0801" "0901" "1001" "1101" "1201")

for FOLDER in "${FOLDERS[@]}"; do
    FILE="${BASE_DIR}/${FOLDER}/concat_monthly/CLM_CFS_${FOLDER}.nc"
    OUTPUT="${BASE_DIR}/${FOLDER}/concat_monthly/CLM_CFS_${FOLDER}_ready.nc"

    if [ -f "$FILE" ]; then
        echo "⏰ Fixing time-of-day in $FILE → $OUTPUT"
        cdo settime,00:00:00 "$FILE" "$OUTPUT"
    else
        echo "⚠️ File not found: $FILE"
    fi
done

echo "✅ Time-of-day updated for all files."

