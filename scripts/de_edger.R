#! /usr/bin/env Rscript

'Perform DE analysis using edgeR

Usage:
  de_edger [--nofilter] --sample-sheet <PATH> --level <TYPE> [--output-dir <PATH>] <count-mat-tsv>

Options:
  --nofilter            : Disable filter [defalt: FALSE]
  --sample-sheet <PATH> : Sample sheet file
  --output-dir <PATH>   : Output directory [default: .]
  --level <TYPE>        : Analysis level (transcript/gene)
  <count-mat-tsv>       : Count matrix file

' -> doc

options(stringAsFactors = FALSE)

# Reading in args
library(docopt)
argv <- docopt(doc)
sample_sheet_path <- argv$`sample-sheet`
output_dir <- argv$`output-dir`
level <- argv$level
count_mat_path <- argv$`count-mat-tsv`

output_dir <- file.path(output_dir, level)

# Requires
library(limma)
library(edgeR)
library(data.table)
library(tidyverse)
library(readr)


# Function definitions
extract_degs <- function(expressions, groups, comparisions, from){
  CUTOFF_RAW  <- 10.0
  results_et <- list()

  # calc dispersion
  dge <- DGEList(counts = expressions, group = groups)

  # NOTE: --nofilter option
  if (!argv$nofilter) {
    keep <- rowSums(dge$counts > CUTOFF_RAW) %>% {. >= min_replicates(groups)}
    dge_filt <- dge[keep, , keep.lib.sizes = FALSE]
  } else {
    dge_filt <- dge
  }

  if (min_replicates(groups) > 1) {
    dge_filt <- calcNormFactors(dge_filt)
    dge_filt <- estimateCommonDisp(dge_filt)
    dge_filt <- estimateTagwiseDisp(dge_filt)
  }
  dge_filt %>% cpm %>% data.frame %>% rownames_to_column(var = 'GeneID') %>% write_tsv_from('expressions_cpm.tsv', from)
  # do exact test (single factor - pairwise)

  expressions_cpm <- dge_filt %>% cpm %>% data.frame %>% rownames_to_column(var = 'GeneID')

  for (i in 1:nrow(comparisions)) {
    s1 <- comparisions[i, ]$sample_1 %>% as.character
    s2 <- comparisions[i, ]$sample_2 %>% as.character

    if (min_replicates(groups) > 1) {
      et <- exactTest(dge_filt, pair = c(s1, s2))
    } else {
      # set squuare root dispersion for human
      message('There is no replication, setting dispersion to typical value.')
      bcv <- 0.4
      et <- exactTest(dge_filt, pair = c(s1, s2), dispersion = bcv^2)
    }
    results_et[[i]] <- et
  }
  return(list(results_et, expressions_cpm))
}

min_replicates <- function (groups) {
  min_samples_per_group <- groups %>% table %>% min %>% as.numeric
  return(min_samples_per_group)
}

write_tsv_from <- function (x, path, from) {
  path <- file.path(from, path)
  x %>% write_tsv(path = path, col_names = TRUE)
}


# Main
## Load data
expressions <- fread(count_mat_path, header = TRUE, sep = '\t', drop = 1) %>% as.matrix
rownames(expressions) <- (fread(count_mat_path, header = TRUE, sep = '\t', select = 1) %>% as.matrix)[, 1]

sample_sheet <- fread(sample_sheet_path, header = TRUE, sep = '\t', stringsAsFactors = FALSE)
groups <- sample_sheet$group
comparisions <- expand.grid(sample_1 = unique(groups), sample_2 = unique(groups), stringsAsFactors = FALSE)

## Create pair-wise comparisions
## HACK: To Simple
keep <- as.numeric(factor(comparisions$sample_1,  levels = unique(groups))) < as.numeric(factor(comparisions$sample_2,  levels = unique(groups)))
comparisions <- comparisions[keep, ]

## Perform exact test
degs <- extract_degs(expressions, groups, comparisions, output_dir)
results_et <- degs[[1]]
expressions_cpm <- degs[[2]]

dir.create(file.path(output_dir), showWarnings = FALSE, recursive = TRUE)

## Merge result tables
table_merged <- data.frame()
for (i in 1:length(results_et)) {
  et <- results_et[[i]]

  comparison <- et$comparison %>% paste(collapse = '_vs_')
  output <- paste0('result_', comparison, '.tsv')
  top_tags <- et %>% topTags(n = nrow(et$table)) %>% as.data.frame

  # export each table
  top_tags <- top_tags %>% rownames_to_column(var = 'GeneID')
  top_tags %>% write_tsv_from(path = output, from = output_dir)

  # export merge table
  colnames(top_tags)[-1] <- paste(comparison, colnames(top_tags)[-1] , sep = '_')
  if (i == 1) {
    table_merged <- top_tags
  } else {
    table_merged <- table_merged %>% left_join(top_tags, by = 'GeneID')
  }
}

## Create TSV
colnames(expressions_cpm)[-1] <- paste(colnames(expressions_cpm)[-1], 'CPM',  sep = '_')
table_merged <- table_merged %>% left_join(expressions_cpm, by = 'GeneID')
table_merged %>% arrange(GeneID) %>% write_tsv_from(path = 'result_comparisions.tsv', from = output_dir)


# Create summary
comparisons <- c()
degs_counts <- c()
for (i in 1:length(results_et)) {
  comparisons <- comparisons %>% c(results_et[[i]]$comparison %>% paste(collapse = '_vs_'))
  degs_counts <- degs_counts %>% c(topTags(results_et[[i]],  n = nrow(results_et[[i]]$table)) %>% as.data.frame %>% rownames_to_column %>% filter(FDR < 0.05 & abs(logFC) > 1) %>% nrow)
}

data.frame(comparison = comparisons, count = degs_counts) %>% write_tsv_from('summary.tsv', from = output_dir)
