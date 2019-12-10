#! /usr/bin/env Rscript
#
# Usage:
#   Rscript this.R <type> <level> [<input_count_data>..]
#
# Options:
#   <output-dir>       : Output directory
#   <type>             : cuffdiff/stringtie/kallisto/rsem
#   <level>            : gene/transcript
#   <input_count_data> : Count (per sample)
#
# Examples:
#   Rscript this.R cuffdiff transcript isoforms.read_group_tracking
#   Rscript this.R kallisto transcript sample_01/abundance.h5 sample_02/abundance.h5
#   Rscript this.R rsem transcript sample_01/quantified.isoforms.results sample_02/quantified.isoforms.results
#   Rscript this.R stringtie transcript sample_01/t_data.ctab sample_02/t_data.ctab

options(stringAsFactors = FALSE)

library(tidyverse)
library(tximport)
library(readr)
library(data.table)


# Reading in args
argv <- commandArgs(TRUE)

if (length(argv) < 3) {
  cat("Usage: conv_any2raw_tximport <type> <level> <input_count_data>...\n")
  q(status = 1)
}

output_dir <- argv[1]
type <- argv[2]
level <- argv[3]
inputs <- argv[-3:-1]

output_dir <- file.path(output_dir, level)

# Function definitions
load_data <- function(type, inputs) {
  if (type == 'cuffdiff') {
    df <- load_cuffdiff(inputs)
    return(df)
  }
  sample_names <- inputs %>% dirname %>% basename
  names(inputs) <- sample_names

  # NOTE: For RSEM recommended befor import cut off non-required columns except 1-8
  # cat rsem.isoforms.results | cut -f 1-8
  txi <- inputs %>% tximport(type = type, txIn = TRUE, txOut = TRUE)
  df <- txi$counts %>% data.frame
  return(df)
}

load_cuffdiff <- function(inputs) {
  input <- inputs[1]
  df <- input %>% fread(sep = '\t')
  df <- df %>% mutate(sample_id = paste0(condition, '_', replicate))
  df <- df %>% select(tracking_id, sample_id, raw_frags)
  df_wide <- df %>% tidyr::spread(key = sample_id, value = raw_frags)
  df_wide <- df_wide %>% column_to_rownames('tracking_id')

  return(df_wide)
}

df <- load_data(type, inputs)
output_path <- file.path(output_dir, 'count_matrix.tsv')
dir.create(dirname(output_path), showWarnings = FALSE, recursive = TRUE)

df %>% write.table(file = output_path, quote = FALSE, sep = '\t', col.names = NA)
