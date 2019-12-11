#! /usr/bin/env Rscript

'Convert any tool results to tximport count matrix

Usage:
  conv_any2raw_tximport --type <TYPE> --level <TYPE> [--output-dir <PATH>] <count-data>...

Options:
  --type <PATH>        : cuffdiff/stringtie/kallisto/rsem
  --level <PATH>       : Analysis level (transcript/gene)
  --output-dir <PATH>  : Output directory [default: .]
  <count-data>         : Count data file(s);
                         (C) isoforms.read_group_tracking, (K) abundance.h5, (R) quantified.isoforms.results, (S) t_data.ctab
' -> doc

options(stringAsFactors = FALSE)

# Reading in args
library(docopt)
argv <- docopt(doc)
output_dir <- argv$`output-dir`
type <- argv$type
level <- argv$level
inputs <- argv$`count-data`

output_dir <- file.path(output_dir, level)


# Requires
library(tidyverse)
library(tximport)
library(readr)
library(data.table)


# Function definitions
load_data <- function(type, inputs) {
  load_cuffdiff <- function(inputs) {
    input <- inputs[1]
    df <- input %>% fread(sep = '\t')
    df <- df %>% mutate(sample_id = paste0(condition, '_', replicate))
    df <- df %>% select(tracking_id, sample_id, raw_frags)
    df_wide <- df %>% tidyr::spread(key = sample_id, value = raw_frags)
    df_wide <- df_wide %>% column_to_rownames('tracking_id')

    return(df_wide)
  }

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

df <- load_data(type, inputs)
output_path <- file.path(output_dir, 'count_matrix.tsv')

dir.create(dirname(output_path), showWarnings = FALSE, recursive = TRUE)

df %>% write.table(file = output_path, quote = FALSE, sep = '\t', col.names = NA)
