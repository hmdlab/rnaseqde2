#! /usr/bin/env Rscript

'Perform DE analysis using edgeR

Usage:
  de_edger [--nofilter] [--gtf <PATH>] --sample-sheet <PATH> [--output-dir <PATH>] <ctab>...

Options:
  --nofilter            : Disable filter [defalt: FALSE]
  --gtf <TYPE>          : GTF file (necessary for RSEM data) [default: #]
  --sample-sheet <PATH> : Sample sheet file
  --output-dir <PATH>   : Output directory [default: .]
  <ctab>...             : Count matrix file(s)

' -> doc

options(stringAsFactors = FALSE)

# Reading in args
library(docopt)
argv <- docopt(doc)
sample_sheet_path <- argv$`sample_sheet`
output_dir <- argv$`output_dir`
gtf <- argv$gtf
ctab <- argv$ctab


# Requires
library(ballgown)
library(genefilter)
library(tidyverse)


## Reading in phenotype data
pheno_data <- read.table(sample_sheet_path, header = TRUE , sep = '\t')
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
  q(status = 1)
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
if (!argv$nofilter) {
  bg_filt <- subset(bg, "rowVars(texpr(bg)) > 1", genomesubset = TRUE)
} else {
  bg_filt <- bg
}

## Detect DEs at transcript-level
results_transcripts <- stattest(bg_filt, feature='transcript', covariate='group', getFC = TRUE, meas='FPKM')

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
dir.create(output_dir, showWarnings = FALSE, recursive = TRUE)

write_tsv(results_transcripts, path = file.path(output_dir, 'result_transcript.tsv'), col_names = TRUE)
write_tsv(results_genes, path = file.path(output_dir, 'result_gene.tsv'), col_names = TRUE)
