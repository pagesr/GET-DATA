#!/bin/bash

BASE_PATH="/Volumes/Desk_SSD/ROMS/RE-FORECAST/GET-DATA/OCN/nc_ocn/2013"

for SUBDIR in 01 02; do
#for SUBDIR in 01 02 03 04 05 06 07 08 09 10 11 12; do
    INPUT_DIR="${BASE_PATH}/${SUBDIR}01"
    OUTPUT_DIR="${INPUT_DIR}/monthly"
    mkdir -p "$OUTPUT_DIR"

    echo ""
    echo "🔁 Processing directory: $INPUT_DIR"
    echo "🔍 Scanning for year-month combinations..."

    year_months=$(find "$INPUT_DIR" -name "data_*.nc" \
        | sed -n 's/.*data_\([0-9]\{4\}\)_\([0-9]\{2\}\)_.*/\1-\2/p' \
        | sort | uniq)

    total_months=$(echo "$year_months" | wc -l)
    counter=0

    echo "$year_months" | while read ym; do
        year=$(echo "$ym" | cut -d'-' -f1)
        month=$(echo "$ym" | cut -d'-' -f2)

        echo "------------------------------------------"
        echo "📅 Year: $year"
        echo "📅 Month: $month"

        files=($(find "$INPUT_DIR" -name "data_${year}_${month}_*.nc" | sort))

        if [ ${#files[@]} -eq 0 ]; then
            echo "⚠️  No files found for $year-$month — skipping."
            continue
        fi

        echo "📦 Averaging ${#files[@]} files for $year-$month..."

        outfile="${OUTPUT_DIR}/data_${year}_${month}_monthly_avg.nc"
        cdo ensmean "${files[@]}" "$outfile"

        echo "✅ Output: $outfile"

        counter=$((counter + 1))
        echo -ne "🧮 Progress: $counter / $total_months months complete\r"
    done

    echo -e "\n✅ Finished: $INPUT_DIR"
done

echo -e "\n🏁 All monthly averages completed for all subdirectories."

