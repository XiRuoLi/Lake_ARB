#!/bin/bash

input_path=$1
output_path=$2
database=$3
listFile=$4
num_jobs=$5


# Check if the correct number of arguments is provided
if [ $# -ne 5 ]; then
echo "Usage: $0 <source_path> <target_path><database> <listFile> <num_jobs>"
exit 1
fi

mkdir $output_path/temp
mkdir $output_path/results

# Function to process a single gzip file
process_bwa() {
local F="$1"

R=${F%_*}_2.fastq.gz
BASE=${F##*/}
SAMPLE=${BASE%_*}
echo $SAMPLE

if grep -qw "$SAMPLE" "$listFile"; then
	if [ -e $output_path/results/${SAMPLE}.bam ]; then
		echo "$SAMPLE SKIP"
	else
    		bwa mem -t 64 $database $F $R > $output_path/temp/${SAMPLE}.bam && python bam_filter.py $output_path/temp/${SAMPLE}.bam $output_path/results/${SAMPLE}.bam && rm $output_path/temp/${SAMPLE}.bam
    		echo "$SAMPLE bwa DONE"
    	fi
else
	echo "$SAMPLE SKIP"
fi

}

#rm -r $output_path/temp

# Use parallel to process gzip files in parallel with specified number of jobs
for F in $input_path/*_1.fastq.gz; do
process_bwa "$F" &
((++processed_files))
[ $((processed_files % num_jobs)) -eq 0 ] && wait
done

