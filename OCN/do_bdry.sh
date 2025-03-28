#!/bin/bash

year=2013

for MONTH in $(seq -w 02 12); do
    echo "📦 Running make_bdry_cfs.py for $MONTH/$year..."
    python3 make_bdry_cfs.py $year/${MONTH}01
done

