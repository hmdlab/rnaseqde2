#! /bin/bash
#
# Quality check for BAM using ReSQC
#
# Usage:
#   find 'mapping/*.bam' | sort | xargs qsub -t 1-n this.sh --bed path/to/bed
#
#$ -S /bin/bash
#$ -l s_vmem=32G -l mem_req=32G
#$ -cwd
#$ -o ugelogs/
#$ -e ugelogs/


# parse option
for opt in "$@"
do
  case $opt in
    '--bed')
      bed=$2
      shift 2
      ;;
    '--output-dir')
      output_dir=$2
      shift 2
      ;;
  esac
done


inputs=($@)
input=${inputs[$((SGE_TASK_ID-1))]}

if [ -z ${output_dir} ]; then
  output_dir="."
fi

mkdir -p ${output_dir}

sample_name=$(basename $(dirname ${input}))

cmd="samtools index \
    ${input}"
echo ${cmd}
eval ${cmd}

script="bam_stat.py"
cmd="${script} \
    -i ${input} \
    > ${output_dir}/${sample_name}.${script/.py/}.txt"
echo ${cmd}
eval ${cmd}

script="read_distribution.py"
cmd="${script} \
    -r ${bed} \
    -i ${input} \
    > ${output_dir}/${sample_name}.${script/.py/}.txt"
echo ${cmd}
eval ${cmd}

script="infer_experiment.py"
cmd="${script} \
    -s 400000 \
    -r ${bed} \
    -i ${input} \
    > ${output_dir}/${sample_name}.${script/.py/}.txt"
echo ${cmd}
eval ${cmd}

script="junction_annotation.py"
cmd="${script} \
    -r ${bed} \
    -i ${input} \
    -o ${output_dir}/${sample_name}"
echo ${cmd}
eval ${cmd}
