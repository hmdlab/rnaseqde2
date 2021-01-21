#! /usr/bin/env Rscript

'Convert cuffdiff results to count matrix

Usage:
  conv_cuffdiff2raw [--output-dir <PATH>] <input>

Options:
  --output-dir <PATH>  : Output directory [default: .]
  <input>              : Cuffdiff result file;
                         isoforms.read_group_tracking or genes.read_group_tracking
' -> doc

# Reading in args
library(docopt)
argv <- docopt(doc)

output_dir <- argv$`output_dir`
input <- argv$`input`

# Requires

library(tidyverse)


# Function definitions
load_data <- function(input) {
  df <- input %>% read_tsv
  df <- df %>% mutate(sample_id = paste0(condition, '_', replicate))
  df <- df %>% select(tracking_id, sample_id, raw_frags)
  df_wide <- df %>% tidyr::spread(key = sample_id, value = raw_frags)
  df_wide <- df_wide %>% column_to_rownames('tracking_id')

  return(df_wide)
}

rslt <- load_data(input)

postfix <- NULL
if (grepl('isoforms', basename(input))) {
  postfix <- 'transcript'
} else if (grepl('genes', basename(input))) {
  postfix <- 'gene'
}

dir.create(output_dir, showWarnings = FALSE, recursive = TRUE)
rslt %>% write.table(file = file.path(output_dir, paste0(paste('count_matrix', postfix, sep = '_'), '.tsv')),
                     quote = FALSE,
                     sep = '\t',
                     col.names = NA)
