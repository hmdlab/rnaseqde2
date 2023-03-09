rnaseqde2
========
RNA-Seq DE analysis pipeline using Universal Grid Engine on NIG supercomputer

## Usage:


```sh
Usage:
    rnaseqde [options] <sample_sheet>

Options:
    --workflow <TYPE>     : Workflow [default: fullset]
    --conf <PATH>         : Directory contain configure files for each tool
    --layout <TYPE>       : Library layout (sr/pe) [default: sr]
    --strandness <TYPE>   : Library strandness (none/rf/fr) [default: none]
    --reference <NAME>    : Reference name [default: grch38]
    --annotation <NAME>   : Annotation name (in the case using only one annotation)
    --step-by-step <TYPE> : Run with step (align/quant/de)
    --assets <PATH>       : Assets yml path
    --resume-from <TYPE>  : Resume workflow from (align/quant/de)
    --ar <ID>             : Advanced Reservation ID (only specify when using UGE)
    --dry-run             : Dry-run [default: False]
    <sample_sheet>        : Tab-delimited text that contained the following columns:
                            sample; fastq1[fastq2]; group

Workflows:
    fullset (default)
    tophat2-cuffdiff
    star-rsem-ebseq
    hisat2-stringtie-ballgown
    kallisto-sleuth
    salmon-deseq2

Supported references:
    grch38 (default)

Supported annotations:
    all (default)
    gencode
    gencode_basic
    gencode_refeseq
```

NOTE: Set the SGE_TASK_ID environment variable to 1 when using this pipeline in a non HPC environment. 
