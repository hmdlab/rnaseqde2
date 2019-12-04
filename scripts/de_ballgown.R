#! /usr/bin/env Rscript
#
# Perform DE analysis using ballgown
#
# Usage:
#   RScript this.R <output_dir> <sample_sheet> <gtf> <ctab>...
#

options(stringAsFactors = FALSE)


library(ballgown)
library(RSkittleBrewer)
library(genefilter)
library(dplyr)
library(readr)


args <- commandArgs(trailingOnly=TRUE)

if (length(args) < 4) {
  stop("Missing arguments\n")
} else {
  output_dir <- args[1]
  sample_sheet <- args[2]
  gtf <- args[3]
  ctab <- args[-(1:3)]
}

## Load phenotype data
pheno_data <- read.table(sample_sheet, header = TRUE, stringsAsFactors = FALSE)
data_files <- dirname(ctab)
names(data_files) <- basename(data_files)

# NOTE: Sort data_files by keys on pheno_data; Unwanted code for the ballgown bug
data_files <- data_files[match(pheno_data[, 1], names(data_files))]

## Read in expression data
if (gtf == '#') {
  message('Run as StringTie mode')
  bg <- ballgown(
    samples = data_files,
    pData = pheno_data
    )
} else {
  # FIXME: NOT work ballgownrsem
  message('Run as RSEM mode')
  stop()
  # bg <- ballgownrsem(
  #   dir = data_dir,
  #   samples = file.path(sample_names, 'quantified'),
  #   gtf = gtf,
  #   pData = pheno_data,
  #   meas = 'TPM'
  #   )
}

## Filter low abundance genes
# NOTE: Is this filter really correct?
bg_filt <- subset(bg, "rowVars(texpr(bg)) > 1", genomesubset = TRUE)

## Detect DEs at transcript-level
results_transcripts <-  stattest(bg_filt, feature='transcript', covariate='group', getFC = TRUE, meas='FPKM')

## Detect DEs at gene-level
results_genes <- stattest(bg_filt, feature='gene', covariate='group', getFC=TRUE, meas='FPKM')

## Add gene name
results_transcripts <- data.frame(
          geneNames = ballgown::geneNames(bg_filt), geneIDs = ballgown::geneIDs(bg_filt),
          transcriptIDs = transcriptNames(bg_filt), results_transcripts
          )

## Sort results from smallest p-value
results_transcripts <- arrange(results_transcripts, pval)
results_genes <- arrange(results_genes, pval)

## Write results to TSV
write_tsv(results_transcripts, path = file.path(output_dir, "transcripts_results.csv"), col_names = TRUE)
write_tsv(results_genes, path = file.path(output_dir, "genes_results.csv"), col_names = TRUE)

## Filter for genes with q-val <0.05 & Write results to TSV
# results_transcripts_de <- subset(results_transcripts, results_transcripts$qval < 0.05)
# results_genes_de <- subset(results_genes, results_genes$qval < 0.05)
# write_tsv(results_transcripts_de, path = file.path(output_dir, "transcripts_results_de.csv"), col_names = TRUE)
# write_tsv(results_genes_de, path = file.path(output_dir, "genes_results_de.csv"), col_names = TRUE)
