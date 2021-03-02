#
# Debug codes for R script
#

# conv_any2raw.R
argv <- list(
  gtf = file.path(Sys.getenv("MH_APP_SHARED"), "assets/references/grch38/annotations/gencode/gencode.v31.annotation.gtf"),
  type = 'stringtie',
  'output-dir' = '.',
  input = unlist(strsplit("gencode/align_star/quant_stringtie/MAQCA_0/t_data.ctab gencode/align_star/quant_stringtie/MAQCA_1/t_data.ctab gencode/align_star/quant_stringtie/MAQCA_2/t_data.ctab", " "))
)


# de_sleuth.R
argv <- list(
  gtf = file.path(Sys.getenv("MH_APP_SHARED"), "assets/references/grch38/annotations/gencode/gencode.v31.annotation.gtf"),
  'output-dir' = '.',
  'sample-sheet' = "sample_sheet.tsv",
  h5 = unlist(strsplit("./MAQCA_1/abundance.h5 ./MAQCB_0/abundance.h5 ./MAQCA_0/abundance.h5 ./MAQCB_1/abundance.h5 ./MAQCA_2/abundance.h5 ./MAQCB_2/abundance.h5", " "))
)

