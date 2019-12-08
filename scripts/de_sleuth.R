#! /usr/bin/env Rscript
#
# Perform DE analysis using ballgown
#

options(stringAsFactors = FALSE)

library(sleuth)
library(tidyverse)
library(rtracklayer)


# Reading in args
argv <- commandArgs(TRUE)

if (length(argv) < 4) {
  cat("Usage: de_sleuth <gtf> <sample_sheet> <output_dir> <kallist_h5>...\n")
  q(status = 1)
}

gtf_path <- argv[1]
sample_sheet_path <- argv[2]
output_dir <- argv[3]
kallisto_h5 <- argv[-(1:3)]

# Reading in sample information
s2c <- read.table(sample_sheet_path, header = TRUE, sep = '\t', stringsAsFactors = FALSE) %>% select(sample, group)

kallisto_dirs <- kallisto_h5 %>% dirname
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

t2g <- load_gtf(gtf_path, cols = c('transcript_id', 'gene_id', 'gene_name'), types = c('exon')) %>% distinct
colnames(t2g) <- c('target_id', 'ensembl_gene', 'ext_gene')

# Reading in kallisto results and then fit the models
so <- sleuth_prep(s2c, ~ group, target_mapping = t2g)
so <- sleuth_fit(so)
so <- sleuth_fit(so, ~1, 'reduced')
so <- sleuth_lrt(so, 'reduced', 'full')

# Show models
models(so)

# To generate a table of results for analysis within R type
results_table <- sleuth_results(so, 'reduced:full', test_type = 'lrt')
results_table %>% write_tsv(file.path(output_dir, 'results.tsv'))
