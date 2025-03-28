#!/bin/bash

# Ensure NCO is installed and available
if ! command -v ncrcat &> /dev/null
then
    echo "NCO (NetCDF Operators) could not be found. Please install NCO to use this script."
    exit
fi

# Directory containing the NetCDF files
base_dir="/Volumes/Desk_SSD/ROMS/RE-FORECAST/GET-DATA/OCN/nc_ocn/"  # Change this if your files are in a different directory
end_dir="$1"
data_dir="${base_dir}${end_dir}/"
data_dir_out="${base_dir}${end_dir}/monthly"
mkdir -p "$data_dir_out"

# Pattern to match the data files
file_pattern="data_????_??_??_??.nc"

# Change to the data directory
cd "$data_dir" || exit

# Get a list of all files matching the pattern
files=$(ls $file_pattern 2> /dev/null)

# Check if any files are found
if [ -z "$files" ]; then
    echo "No files matching the pattern '$file_pattern' found in $data_dir."
    exit
fi

# Extract unique year-month combinations from filenames
year_month_list=$(ls $file_pattern | awk -F'_' '{print $2"_"$3}' | sort | uniq)

# Loop over each unique year-month
for year_month in $year_month_list; do
    year=$(echo $year_month | cut -d'_' -f1)
    month=$(echo $year_month | cut -d'_' -f2)

    echo "Processing month: $year-$month"

    # Find all files for the current year and month
    month_files=$(ls data_${year}_${month}_??_??.nc 2> /dev/null)

    # Check if any files are found for this month
    if [ -z "$month_files" ]; then
        echo "No files found for month $year-$month. Skipping..."
        continue
    fi

    # Temporary concatenated file
    concat_file="data_${year}_${month}_concat.nc"
    # Output filename for the monthly average
    output_file="data_${year}_${month}_monthly_avg.nc"

    # Concatenate files along the record (time) dimension
    ncrcat $month_files $concat_file

    # Compute the average over the time dimension
    ncra $concat_file ${data_dir_out}/$output_file

    # Remove temporary concatenated file
    rm $concat_file

    # Check if the output file was created successfully
    if [ -f "$output_file" ]; then
        echo "Monthly average for $year-$month computed successfully: $output_file"
    else
        echo "Failed to compute monthly average for $year-$month."
    fi
done
