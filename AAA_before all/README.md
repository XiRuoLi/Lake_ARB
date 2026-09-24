# ARG Quantification Using RGI

This repository contains shell scripts for antibiotic resistance gene (ARG) profiling using the RGI workflow from the Comprehensive Antibiotic Resistance Database (CARD).


## Paired-end reads

`RGI_reads_paired.sh`

Processes paired-end metagenomic sequencing data (`*_1.fastq.gz` and `*_2.fastq.gz`).

## Single-end reads

`RGI_reads_single.sh`

Processes single-end metagenomic sequencing data (`*.fastq.gz`).

---

# Lake Resistome MAG Analysis Pipeline

This repository contains scripts used for metagenome-assembled genome (MAG) analysis, including mobile genetic element (MGE) annotation, virulence factor (VF) annotation, MAG dereplication, and MAG abundance quantification from metagenomic sequencing data.

---

## 1. MGE Annotation

`MGE_annotation.txt`

Mobile genetic element (MGE)-associated proteins are identified by searching predicted protein sequences against the MobileOG database using DIAMOND.

### Input

- Predicted protein sequences (`*.faa`)
- MobileOG protein database

### Output

- Tabular annotation file containing MGE matches

### Usage

Prepare the MobileOG database and provide the predicted protein sequences generated from MAGs or metagenomic assemblies. The script performs DIAMOND-based protein annotation and exports all matches that satisfy the predefined identity, coverage, and e-value thresholds.

---

## 2. VF Annotation

`VF_annotation.txt`

Virulence factors (VFs) are identified by searching predicted protein sequences against the VFDB database using DIAMOND.

### Input

- Predicted protein sequences (`*.faa`)
- VFDB protein database

### Output

- Tabular annotation file containing VF matches

### Usage

Prepare the VFDB database and provide the predicted protein sequences. The script performs protein-level similarity searches and reports putative virulence factors that pass the specified filtering criteria.

---

## 3. MAG Dereplication

`MAG_dereplication.txt`

Redundant MAGs are removed using dRep based on Average Nucleotide Identity (ANI).

### Input

- MAG genome files (`*.fa`)

### Output

- Non-redundant representative MAGs
- Genome clustering information

### Usage

Place all MAG genome files in a single directory and specify the input and output paths. The workflow clusters genomes using FastANI and retains representative genomes according to the user-defined similarity thresholds.

---

## 4. MAG Abundance Quantification
`MAG_abundance_calculation`

`1.bwa_and_filter_if.sh`

`2.bam_to_abundance_nofilter.sh`

MAG abundance is estimated by mapping metagenomic reads to reference genomes, followed by abundance calculation with CoverM.

### Input

- Paired-end metagenomic reads
- Reference MAG genomes
- MAG-to-contig mapping file

### Output

- Filtered BAM files
- MAG abundance tables

### Usage

First, map sequencing reads to the reference genomes and generate filtered BAM files. Next, use the abundance script to rarefy sequencing depth, calculate genome coverage statistics, and estimate MAG abundance with CoverM.

The abundance workflow reports multiple metrics, including read counts, covered fraction, trimmed mean coverage, and RPKM values.

---
