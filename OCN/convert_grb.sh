#!/bin/bash
year=2013
logfile="logs/convert_grib_${year}_full.log"
mkdir -p logs

for MONTH in $(seq -w 02 12); do
    echo "Compute $MONTH for $year" | tee -a "$logfile"
    python3 -u grb_2_netcdf.py $year/${MONTH}01 >> "$logfile" 2>&1
done


