#! /usr/bin/env Rscript

'Perform DE analysis using EBSeq
  This script is modified version of rsem-for-ebseq-find-DE.R
  https://github.com/deweylab/RSEM/blob/master/EBSeq/rsem-for-ebseq-find-DE

Usage:
  rsem-for-ebseq-find-DE  [--ngvector <PATH>] --level <TYPE> [--output-dir <PATH>] <count-mat-tsv> <n_rep1> <n_rep2>

Options:
  --ngvector <PATH>            : NgVector file [defaul: #]
  --level <TYPE>               : Analysis level (transcript/gene)
  --output-dir <PATH>          : Output directory [default: .]
  <count-mat-tsv>              : Count matrix file
  <n_rep1>                     : N replicates of Group 1
  <n_rep2>                     : N replicates of Group 2

' -> doc

options(stringAsFactors = FALSE)

# Reading in args
library(docopt)
argv <- docopt(doc)

ngvector_file <- argv$`ngvector`
data_matrix_file <- argv$`count_mat_tsv`
output_dir <- argv$`output_dir`
output_file <- file.path(output_dir, "result.tsv")
norm_out_file <- paste0(output_file, ".normalized_data_matrix")


# Requires
library(EBSeq)


# CHANGE: Fixed length args
nc <- 2
num_reps <- as.numeric(c(argv$n_rep1, argv$n_rep2))

# Reading in count data & test
DataMat <- data.matrix(read.table(data_matrix_file))
n <- dim(DataMat)[2]
if (sum(num_reps) != n) stop("Total number of replicates given does not match the number of columns from the data matrix!")

conditions <- as.factor(rep(paste("C", 1:nc, sep=""), times = num_reps))
Sizes <- MedianNorm(DataMat)
NormMat <- GetNormalizedMat(DataMat, Sizes)
ngvector <- NULL

if (ngvector_file != "#") {
  # CHANGE: Due to sort,  a single column to two columns
  ngvector <- as.vector(data.matrix(read.table(ngvector_file)$V2))
  names(ngvector) <- as.vector(read.table(ngvector_file)$V1)
  ngvector <- ngvector[rownames(DataMat)]
  stopifnot(!is.null(ngvector))
}

dir.create(output_dir, showWarnings = FALSE, recursive = TRUE)

if (nc == 2) {
  EBOut <- NULL
  EBOut <- EBTest(Data = DataMat, NgVector = ngvector, Conditions = conditions, sizeFactors = Sizes, maxround = 5)
  stopifnot(!is.null(EBOut))
  PP <- as.data.frame(GetPPMat(EBOut))
  fc_res <- PostFC(EBOut)
  results <- cbind(PP, fc_res$PostFC, fc_res$RealFC,unlist(EBOut$C1Mean)[rownames(PP)], unlist(EBOut$C2Mean)[rownames(PP)])
  colnames(results) <- c("PPEE", "PPDE", "PostFC", "RealFC","C1Mean","C2Mean")
  results <- results[order(results[,"PPDE"], decreasing = TRUE),]
  write.table(results, file = output_file, sep = "\t")
}

write.table(NormMat, file = norm_out_file, sep = "\t")
