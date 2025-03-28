#!/bin/bash

# 📆 Define the year
YEAR=2013

# 📁 Base directory (uses $YEAR)
BASE_DIR="/Volumes/Desk_SSD/ROMS/RE-FORECAST/GET-DATA/OCN/clm/${YEAR}"

# Define the month-day folders
FOLDERS=("0101" "0201" "0301" "0401" "0501" "0601" "0701" "0801" "0901" "1001" "1101" "1201")

# Loop through each folder
for FOLDER in "${FOLDERS[@]}"; do
    echo "Processing folder: $FOLDER"

    # Define the working directory using BASE_DIR
    WORKDIR="${BASE_DIR}/${FOLDER}/concat_monthly"

    # Ensure the working directory exists
    if [ ! -d "$WORKDIR" ]; then
        echo "Skipping $FOLDER: Directory $WORKDIR does not exist."
        continue
    fi

    # Move into the directory
    cd "$WORKDIR" || exit

    # Define the NetCDF file for the month
    MONTH=${FOLDER:0:2}  # Extract month
    INPUT_FILE="CLM_CFS_${YEAR}_${MONTH}.nc"
    OUTPUT_FILE="CLM_CFS_${FOLDER}.nc"

    # Check if the input file exists
    if [ ! -f "$INPUT_FILE" ]; then
        echo "File $INPUT_FILE does not exist in $WORKDIR. Skipping..."
        cd - > /dev/null
        continue
    fi

    echo "Updating time reference for $INPUT_FILE to start at ${YEAR}-${MONTH}-01 00:00:00..."

    # Step 1: Set reference time before concatenation
    cdo setreftime,1900-01-01,00:00:00,days -settime,00:00:00 -setdate,${YEAR}-${MONTH}-01 "$INPUT_FILE" "$INPUT_FILE.tmp"
    mv "$INPUT_FILE.tmp" "$INPUT_FILE"

    # Step 2: Concatenate all relevant NetCDF files
    echo "Concatenating files in $WORKDIR..."
    cdo cat CLM_CFS_*.nc "$OUTPUT_FILE"

    echo "Saved concatenated file: $OUTPUT_FILE"

    # Return to the original directory
    cd - > /dev/null
done

echo "All folders processed!"

