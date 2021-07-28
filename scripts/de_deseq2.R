#! /usr/bin/env Rscript

'Perform DE analysis using DESeq2

Usage:
  de_deseq2.R [--nofilter] --sample-sheet <PATH> [--output-dir <PATH>] <count-mat-tsv>

Options:
  --nofilter            : Disable filter [defalt: FALSE]
  --sample-sheet <PATH> : Sample sheet file
  --output-dir <PATH>   : Output directory [default: .]
  <count-mat-tsv>       : Count matrix file

' -> doc


library(DESeq2)
library(tidyverse)


options(stringAsFactors = FALSE)

# DEBUG:
# argv <- list(
#   "nofilter" = FALSE,
#   "sample_sheet" = "/home/yh0000549848/projects/pj04f_eval_rnaseqde_map/results/test01_main_r/sample_sheet_MAIN.tsv",
#   "output_dir" = "/home/yh0000549848/projects/pj04f_eval_rnaseqde_map/results/test01_main_r/gencode/quant_salmon/conv_any2raw/de_deseq2",
#   "count_mat_tsv" = "/home/yh0000549848/projects/pj04f_eval_rnaseqde_map/results/test01_main_r/gencode/quant_salmon/conv_any2raw/count_matrix_transcript.tsv"
# )

argv <- docopt::docopt(doc)
sample_sheet_path <- argv$`sample_sheet`
output_dir <- argv$`output_dir`
count_mat_path <- argv$`count_mat_tsv`

CUTOFF_RAW <- 10

count_mat <- read_tsv(count_mat_path) %>%
  column_to_rownames("X1") %>%
  apply(c(1, 2), ceiling)

meta <- read_tsv(sample_sheet_path) %>%
  select(sample, group) %>%
  column_to_rownames("sample")

groups <- unique(meta$group)
meta <- meta[match(colnames(count_mat), rownames(meta)), , drop = FALSE] %>%
  mutate(group = factor(group, levels = groups))

contrasts <-
  expand.grid(
    group_1 = groups,
    group_2 = groups,
    stringsAsFactors = FALSE
  )

keep <-
  as.numeric(factor(contrasts$group_1, levels = groups)) < as.numeric(factor(contrasts$group_2, levels = groups))
contrasts <- contrasts[keep, ]

dds <- DESeqDataSetFromMatrix(countData = count_mat,
                              colData = meta,
                              design = ~ group)

.min_replicates <- function(groups) {
  groups %>%
    table %>%
    min %>%
    as.numeric
}

if (!argv$nofilter) {
  keep <- rowSums(counts(dds) > CUTOFF_RAW) %>% { . >= .min_replicates(meta$group) }
  dds <- dds[keep,]
}

dds <- estimateSizeFactors(dds)
dds <- estimateDispersions(dds)

count_mat_norm <- counts(dds, normalized = TRUE)

dds.wald <- nbinomWaldTest(dds)

results_wald <- map2(
  contrasts$group_1,
  contrasts$group_2,
  ~ results(dds.wald, contrast = c("group", .y, .x))
) %>% set_names(paste(contrasts$group_1, contrasts$group_2, sep = '_vs_'))

.save_deseq2 <- function(x, basename) {
  x %>%
    data.frame %>%
    arrange(padj) %>%
    rownames_to_column(var = "feature_id") %>%
    write_tsv(file.path(output_dir, basename))
}

map2(results_wald,
     names(results_wald),
     ~ .save_deseq2(.x, paste0("wald_", .y, ".tsv")))

count_mat_norm %>%
  data.frame %>%
  write_tsv(file.path(output_dir, "count_mat_norm.tsv"))
