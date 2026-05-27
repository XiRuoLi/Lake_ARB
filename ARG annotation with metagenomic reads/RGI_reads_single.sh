#!/bin/bash

input_path=$1
output_path=$2
num_jobs=$3

# Check if the correct number of arguments is provided
if [ $# -ne 3 ]; then
echo "Usage: $0 <source_path> <target_path> <num_jobs>"
exit 1
fi

# Function to process a single gzip file
rgi_bwt () {
local F="$1"

BASE=${F##*/}
SAMPLE=${BASE%_*}
echo $SAMPLE
echo $F

if [ -e $output_path/${SAMPLE}.overall_mapping_stats.txt ]; then
    echo "$BASE SKIP"
else
    rgi bwt -1 $F --aligner bwa --output_file $output_path/${SAMPLE} --threads 64 --clean --local
    echo "$BASE rgi DONE"
fi

}

# Use parallel to process gzip files in parallel with specified number of jobs
for F in $input_path/*.fastq.gz; do
rgi_bwt $F &
((++processed_files))
[ $((processed_files % num_jobs)) -eq 0 ] && wait
done

wait

