#! /usr/bin/env Rscript

"Perform DE analysis using ballgown

Usage:
  de_ballgown.R [--nofilter] [--gtf <PATH>] --sample-sheet <PATH> [--output-dir <PATH>] <ctab>...

Options:
  --nofilter            : Disable filter [defalt: FALSE]
  --gtf <TYPE>          : GTF file (necessary for RSEM data) [default: #]
  --sample-sheet <PATH> : Sample sheet file
  --output-dir <PATH>   : Output directory [default: .]
  <ctab>...             : Count matrix file(s)

" -> doc


library(ballgown)
library(genefilter)
library(tidyverse)


options(stringAsFactors = FALSE)

argv <- docopt::docopt(doc)
sample_sheet_path <- argv$`sample_sheet`
output_dir <- argv$`output_dir`
gtf <- argv$gtf
ctab <- argv$ctab


pheno_data <-
  read.table(sample_sheet_path, header = TRUE , sep = "\t")
data_files <- dirname(ctab)
names(data_files) <- basename(data_files)

data_files <- data_files[match(pheno_data[, 1], names(data_files))]

if (gtf == "#") {
  message("Run as StringTie mode")
  bg <- ballgown(samples = data_files,
                 pData = pheno_data)
} else {
  # FIXME: NOT work ballgownrsem
  message("Run as RSEM mode")
  q(status = 1)
}

if (!argv$nofilter) {
  bg_filt <- subset(bg, "rowVars(texpr(bg)) > 1", genomesubset = TRUE)
} else {
  bg_filt <- bg
}

results_transcripts <-
  stattest(
    bg_filt,
    feature = "transcript",
    covariate = "group",
    getFC = TRUE,
    meas = "FPKM"
  )

results_genes <-
  stattest(
    bg_filt,
    feature = "gene",
    covariate = "group",
    getFC = TRUE,
    meas = "FPKM"
  )

results_transcripts <- data.frame(
  geneNames = ballgown::geneNames(bg_filt),
  geneIDs = ballgown::geneIDs(bg_filt),
  transcriptIDs = transcriptNames(bg_filt),
  results_transcripts
)

results_transcripts <- arrange(results_transcripts, pval)
results_genes <- arrange(results_genes, pval)

dir.create(output_dir, showWarnings = FALSE, recursive = TRUE)

write_tsv(
  results_transcripts,
  path = file.path(output_dir, "result_transcript.tsv"),
  col_names = TRUE
)
write_tsv(
  results_genes,
  path = file.path(output_dir, "result_gene.tsv"),
  col_names = TRUE
)
