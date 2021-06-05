#! /usr/bin/env Rscript

"Perform DE analysis using edgeR

Usage:
  de_edger.R [--nofilter] --sample-sheet <PATH> [--output-dir <PATH>] <count-mat-tsv>

Options:
  --nofilter            : Disable filter [defalt: FALSE]
  --sample-sheet <PATH> : Sample sheet file
  --output-dir <PATH>   : Output directory [default: .]
  <count-mat-tsv>       : Count matrix file

" -> doc


library(edgeR)
library(tidyverse)


options(stringAsFactors = FALSE)

argv <- docopt::docopt(doc)
sample_sheet_path <- argv$`sample_sheet`
output_dir <- argv$`output_dir`
count_mat_path <- argv$`count_mat_tsv`

CUTOFF_RAW <- 10.0

count_mat <-
  read.table(
    count_mat_path,
    header = TRUE,
    sep = "\t",
    row.names = 1,
    stringsAsFactors = FALSE
  ) %>%
  as.matrix %>%
  apply(c(1, 2), ceiling)

count_mat <- count_mat[, c(1, 4)]

sample_sheet <-
  read.table(
    sample_sheet_path,
    header = TRUE,
    sep = "\t",
    stringsAsFactors = FALSE
  )
groups <- sample_sheet$group %>%
  set_names(sample_sheet$sample)

contrasts <- expand.grid(
  group_1 = unique(groups),
  group_2 = unique(groups),
  stringsAsFactors = FALSE
)
keep <-
  as.numeric(factor(contrasts$group_1, levels = unique(groups))) > as.numeric(factor(contrasts$group_2, levels = unique(groups)))

contrasts <- contrasts[keep,]

groups <- groups[colnames(count_mat)]
y <- DGEList(counts = count_mat, group = groups)

.min_replicates <- function(groups) {
  groups %>%
    table %>%
    min %>%
    as.numeric
}

if (!argv$nofilter) {
  keep <-
    rowSums(y$counts > CUTOFF_RAW) %>% {
      . >= .min_replicates(groups)
    }
  y <- y[keep, , keep.lib.sizes = FALSE]
}

y <- calcNormFactors(y)

if (.min_replicates(groups) > 1) {
  y <- estimateCommonDisp(y)
  y <- estimateTagwiseDisp(y)
}

log2cpm_mat_norm <- y %>%
  cpm(log = TRUE, normalized.lib.sizes = TRUE) %>%
  data.frame %>%
  rownames_to_column(var = "feature_id")

if (.min_replicates(groups) <= 1) {
  message(
    "The experiment has no replicates, set the constant to a dispersion parameter (0.4 for humans)."
  )
  .dispersion <- 0.4 ^ 2
} else {
  .dispersion <- "auto"
}

results_et <- map2(
  contrasts$group_1,
  contrasts$group_2,
  ~ exactTest(y, pair = c(.y, .x), dispersion = .dispersion)
) %>% set_names(paste(contrasts$group_1, contrasts$group_2, sep = "_vs_"))

dir.create(file.path(output_dir),
           showWarnings = FALSE,
           recursive = TRUE)

.save_edger <- function(x, output_path) {
  x %>%
    topTags(., n = nrow(.)) %>%
    data.frame %>%
    rownames_to_column(var = "feature_id") %>%
    write_tsv(output_path)
}

map2(results_et,
     names(results_et),
     ~ .save_edger(.x, file.path(output_dir, paste0("et_", .y, ".tsv"))))

log2cpm_mat_norm %>%
  write_tsv(file.path(output_dir, "log2cpm_mat_norm.tsv"))
