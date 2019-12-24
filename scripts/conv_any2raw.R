#! /usr/bin/env Rscript

'Convert any tool results to tximport count matrix

Usage:
  conv_any2raw_tximport --gtf <PATH> --type <TYPE> [--output-dir <PATH>] <input>...

Options:
  --gtf <PATH>         : GTF file
  --type <PATH>        : stringtie/kallisto/rsem
  --output-dir <PATH>  : Output directory [default: .]
  <input>              : Count data file;
                         (K) abundance.h5, (R) quantified.isoforms.results, (S) t_data.ctab
' -> doc

# Reading in args
library(docopt)
argv <- docopt(doc)

gtf_path <- argv$gtf
output_dir <- argv$`output-dir`
type <- argv$type
inputs <- argv$input


# Requires
library(tximport)
library(rtracklayer)
library(tidyverse)


# Function definitions
load_data <- function(type, inputs, t2g) {
  sample_names <- inputs %>% dirname %>% basename
  names(inputs) <- sample_names

  # NOTE: For RSEM recommended befor import cut off non-required columns except 1-8
  # cat rsem.isoforms.results | cut -f 1-8
  txi.tx <- inputs %>% tximport(type = type, txIn = TRUE, txOut = TRUE)
  txi.gene <- txi.tx %>% summarizeToGene(t2g)

  results <- list(
    tx = data.frame(txi.tx$counts),
    gene = data.frame(txi.gene$counts)
  )

  return(results)
}

load_gtf <- function(path, cols, types = c('transcript')) {
  gtf <- path %>% readGFF(version = 2L, tags = cols, filter = list(type = types))
  gtf <- gtf %>% select(cols)
  return(gtf)
}

t2g <- load_gtf(
  gtf_path,
  cols = c('transcript_id', 'gene_id', 'gene_name'),
  types = c('exon')) %>% distinct

results <- load_data(type, inputs, t2g)

dir.create(output_dir, showWarnings = FALSE, recursive = TRUE)
results$tx %>% write.table(file = file.path(output_dir, 'count_matrix_transcript.tsv'),
                           quote = FALSE,
                           sep = '\t',
                           col.names = NA)

results$gene %>% write.table(file = file.path(output_dir,'count_matrix_gene.tsv'),
                             quote = FALSE,
                             sep = '\t',
                             col.names = NA)
