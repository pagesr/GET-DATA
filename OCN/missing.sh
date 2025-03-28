#!/bin/bash
year=2013

for MONTH in $(seq -w 02 12); do
    echo "Cleaning macOS metadata files for $MONTH/$year..."
    find nc_ocn/$year/${MONTH}01 -name "._*" -type f -delete

    echo "Running patch for $MONTH/$year..."
    python3 missing_files.py $year/${MONTH}01
done

