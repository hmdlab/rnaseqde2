#! /usr/bin/env Rscript

'Perform DE analysis using sleuth

Usage:
  de_sleuth --gtf <PATH> --sample-sheet <PATH> [--output-dir <PATH>] <h5>...

Options:
  --gtf <TYPE>          : GTF file (necessary for RSEM data) [default: #]
  --sample-sheet <PATH> : Sample sheet file
  --output-dir <PATH>   : Output directory [default: .]
  <h5>...               : Kallisto h5 result file(s)

' -> doc

# Reading in args
library(docopt)
argv <- docopt(doc)

sample_sheet_path <- argv$`sample-sheet`
output_dir <- argv$`output-dir`
gtf_path <- argv$gtf
kallisto_h5_path <- argv$h5

# Requires
library(sleuth)
library(rtracklayer)
library(tidyverse)

# Reading in sample information
s2c <- read.table(
  sample_sheet_path,
  header = TRUE,
  sep = '\t',
  stringsAsFactors = FALSE) %>% select(sample, group)

kallisto_dirs <- kallisto_h5_path %>% dirname
names(kallisto_dirs) <- kallisto_dirs %>% basename

## NOTE: Sort kallisto_dirs by keys on sample sheet
kallisto_dirs <- kallisto_dirs[match(s2c[, 1], names(kallisto_dirs))]
s2c$path <- as.character(kallisto_dirs)

# Reading in transcript-gene annotation relationship
load_gtf <- function(path, cols, types = c('transcript')) {
  gtf <- path %>% readGFF(version = 2L, tags = cols, filter = list(type = types))
  gtf <- gtf %>% select(cols)
  return(gtf)
}

t2g <- load_gtf(
  gtf_path,
  cols = c('transcript_id', 'gene_id', 'gene_name'),
  types = c('exon')) %>% distinct

colnames(t2g) <- c('target_id', 'ens_gene', 'ext_gene')

# Reading in kallisto results and then fit the models
so <- sleuth_prep(s2c,
                  ~group,
                  target_mapping = t2g,
                  aggregation_column = 'ens_gene',
                  extra_bootstrap_summary = TRUE)
so <- sleuth_fit(so)
so <- sleuth_fit(so, ~1, 'reduced')
so <- sleuth_lrt(so, 'reduced', 'full')

# Show models
models(so)

# To generate a table of results for analysis within R type

sleuth_table_gene <- sleuth_results(so, 'reduced:full', test_type = 'lrt', show_all = FALSE)
sleuth_table_gene %>% write_tsv(file.path(output_dir, 'result_gene.tsv'))

results_table_tx <- sleuth_results(so, 'reduced:full', test_type = 'lrt', show_all = FALSE,  pval_aggregate = FALSE)
results_table_tx %>% write_tsv(file.path(output_dir, 'result_transcript.tsv'))

