#!/bin/bash

# Check arguments
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <BAM_DIR> <MAP_FILE> <OUT_DIR>"
    echo "Example: $0 ./bam_files mag_to_contig.tsv ./Final_Results"
    exit 1
fi

# ================= Configuration =================
INPUT_DIR="$1"
MAP_FILE="$2"
OUT_DIR="$3"

# Target rarefaction depth
MIN_DEPTH=110000

mkdir -p "$OUT_DIR"
# ===============================================

echo "=== Processing Loop (Subsampling -> CoverM) ==="

for bam in "${INPUT_DIR}"/*.bam; do
    [ -e "$bam" ] || continue
    
    SAMPLE=$(basename "$bam" .bam)
    echo "[Processing $SAMPLE]"

    # --- Get the total number of reads in the current BAM file ---
    echo "  -> Estimating current depth..."
    CURRENT_DEPTH=$(samtools view -c "$bam")

    # --- 2.2 Calculate subsampling factor  ---
    FACTOR=$(awk -v t="$MIN_DEPTH" -v c="$CURRENT_DEPTH" 'BEGIN {if (c>0) printf "%.6f", t/c; else print "0"}')
    
    if (( $(echo "$FACTOR > 1.0" | bc -l) )); then 
        FACTOR="1.0"
        echo "  -> Note: Sample depth ($CURRENT_DEPTH) is below target. No subsampling."
    fi
    
    SUBSAMPLE_PARAM="100${FACTOR}"
    
    # Perform subsampling and sort BAM
    TEMP_BAM="${OUT_DIR}/${SAMPLE}.temp.bam"
    echo "  -> Subsampling to factor: $FACTOR"
    samtools view -s "$SUBSAMPLE_PARAM" -b "$bam" | samtools sort - -o "$TEMP_BAM"
    samtools index "$TEMP_BAM"

    # Quantify MAG abundance using CoverM
    echo "  -> Running CoverM..."
    FINAL_STATS="${OUT_DIR}/${SAMPLE}.final_stats.txt"
    
    coverm genome \
        --bam-files "$TEMP_BAM" \
        --genome-definition "$MAP_FILE" \
        --output-format sparse \
        --methods trimmed_mean covered_fraction count rpkm \
        --trim-min 5 --trim-max 95 \
        --min-covered-fraction 0 \
        --output-file "$FINAL_STATS"

    rm "$TEMP_BAM" "${TEMP_BAM}.bai"
    
    echo "  -> Done. Saved to $FINAL_STATS"
done

echo "=== All Analysis Finished ==="