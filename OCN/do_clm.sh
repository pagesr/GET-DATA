#!/bin/bash

# 📆 Year to process
Y=2013

# 📁 Base path for CLM files
BASE_DIR="/Volumes/Desk_SSD/ROMS/RE-FORECAST/GET-DATA/OCN/clm/${Y}"

# 🔁 Loop through each month (01 to 12)
# for month in $(seq -w 1 12); do
for month in 03; do
    echo "📦 Processing: $Y/${month}01"

    # 🔹 Step 1: Run the CLM creation script
     python3 -u make_clm_file.py "$Y/${month}01"

    # 🔹 Step 2: Setup paths
    path_file="${BASE_DIR}/${month}01/"
    output_dir="${path_file}concat_monthly/"
    mkdir -p "$output_dir"

    # 🔹 Step 3: Create list of *_sshg_clim_NWGOA3.nc files (if they exist)
    find "$path_file" -type f -name "*_sshg_clim_NWGOA3.nc" -exec basename {} \; > list.txt

    # 🔒 If no files found, skip this month
    if [ ! -s list.txt ]; then
        echo "⚠️  No sshg CLM files found for $Y-$month — skipping."
        echo "--------------------------------------------"
        continue
    fi

    # 📂 Read filenames into array
    list=()
    while IFS= read -r line; do
        list+=("$line")
    done < list.txt

    for l in "${list[@]}"; do
        echo "🔍 Processing file: $l"

        # Remove prefix and extract year/month
        filename="${l#data_}"
        year_month="${filename%%_monthly_avg_*}"
        year="${year_month%%_*}"
        file_month="${year_month##*_}"

        echo "📅 Year: $year, Month: $file_month"

        # 🔗 Define all variable files
        sshg_file="${path_file}data_${year}_${file_month}_monthly_avg_sshg_clim_NWGOA3.nc"
        thetao_file="${path_file}data_${year}_${file_month}_monthly_avg_thetao_clim_NWGOA3.nc"
        so_file="${path_file}data_${year}_${file_month}_monthly_avg_so_clim_NWGOA3.nc"
        u_file="${path_file}data_${year}_${file_month}_monthly_avg_u_clim_NWGOA3.nc"
        v_file="${path_file}data_${year}_${file_month}_monthly_avg_v_clim_NWGOA3.nc"

        # 📦 Output file
        concatenated_file="${output_dir}CLM_CFS_${year}_${file_month}.nc"

        # 🔍 Check all required files exist
        variable_files=("$sshg_file" "$thetao_file" "$so_file" "$u_file" "$v_file")
        missing_files=()
        for var_file in "${variable_files[@]}"; do
            [ ! -f "$var_file" ] && missing_files+=("$var_file")
        done

        if [ ${#missing_files[@]} -ne 0 ]; then
            echo "🚫 Missing files for ${year}-${file_month}:"
            for mf in "${missing_files[@]}"; do echo "  - $mf"; done
            echo "⏭️  Skipping concatenation for ${year}-${file_month}."
            continue
        fi

        # 🔗 Concatenate files
        echo "🔗 Concatenating for ${year}-${file_month}..."
        ncks -a -O "$sshg_file" "$concatenated_file"
        ncks -a -A "$thetao_file" "$concatenated_file"
        ncks -a -A "$so_file" "$concatenated_file"
        ncks -a -A "$u_file" "$concatenated_file"
        ncks -a -A "$v_file" "$concatenated_file"

        echo "✅ Created: $concatenated_file"
    done

    # 🧹 Clean up
    rm -f list.txt
    echo "✅ Completed month: $month"
    echo "--------------------------------------------"
done

echo "🎉 All months processed!"


# 📍 Final merge per folder
echo "🧩 Final monthly merge per folder..."

# ⏩ Loop over all 0101, 0201... directories
for folder in "${BASE_DIR}"/*; do
    FOLDER=$(basename "$folder")
    MERGE_DIR="${BASE_DIR}/${FOLDER}/concat_monthly"

    if [ ! -d "$MERGE_DIR" ]; then
        echo "⏭️  Skipping $FOLDER (no concat_monthly dir)"
        continue
    fi

    cd "$MERGE_DIR" || continue

    # Output file: one file per FOLDER like CLM_CFS_0101.nc
    FINAL_FILE="CLM_CFS_${FOLDER}.nc"

    # Find all monthly files
    MONTHLY_FILES=$(ls CLM_CFS_20*.nc 2>/dev/null)

    if [ -z "$MONTHLY_FILES" ]; then
        echo "⚠️  No monthly CLM files found in $MERGE_DIR"
        cd - > /dev/null
        continue
    fi

    echo "📦 Concatenating monthly files into $FINAL_FILE..."
    cdo cat $MONTHLY_FILES "$FINAL_FILE"
    echo "✅ Saved: $MERGE_DIR/$FINAL_FILE"

    cd - > /dev/null
done

echo "🎯 Final concatenation complete!"
./concat_clm.sh
./change_time.sh
