#! /usr/bin/env python3
#$ -S $HOME/.pyenv/shims/python3
#$ -pe def_slot 4
#$ -l s_vmem=16G -l mem_req=16G
#$ -cwd
#$ -o ugelogs/
#$ -e ugelogs/

import sys
import os
import subprocess
from textwrap import dedent

import rnaseqde.utils as utils
from rnaseqde.task.base import ArrayTask


class QuantRsemTask(ArrayTask):
    instances = []

    @property
    def inputs(self):
        inputs_ = {'--output-dir': self.output_dir}

        binding = {
                '--index': '--rsem-index',
                '--layout': '--layout',
                '--strandness': '--strandness',
                '--dry-run': '--dry-run',
                '--transcript-bam': '--transcript-bam'
                }

        inputs_ = utils.dictbind(inputs_, super().inputs, binding)

        return inputs_

    def output_subdir(self, input):
        subdir_ = os.path.join(
            self.output_dir,
            os.path.basename(os.path.dirname(input))
        )

        return subdir_

    def output_prefix(self, input):
        prefix_ = os.path.join(self.output_subdir(input), 'quantified')

        return prefix_

    @property
    def outputs(self):
        bams = self.inputs['--transcript-bam']

        binding = {
            '--gene-tsv': '.genes.results',
            '--transcript-tsv': '.isoforms.results',
            '--stat': '.stat'
        }

        dict_ = super().inputs

        for k, v in binding.items():
            dict_[k] = [self.output_prefix(s) + v for s in bams]

        return dict_


def main():
    """
    Wrapper for UGE: Quantify transcript abundance using RSEM

    Usage:
        quant_rsem [options] --index <PATH> --transcript-bam <PATH>...

    Options
        --index <PATH>              : Reference index file
        --layout <TYPE>             : Library layout (sr/pe) [default: sr]
        --strandness <TYPE>         : Library strandness (none/rf/fr) [default: none]
        --output-dir <PATH>         : Output directory [default: .]
        --conf <PATH>               : Configuration file
        --dry-run                   : Dry-run [default: False]
        --transcript-bam <PATH>...  : BAM file mapped to Transcriptome

    Example:
        rsem-calculate-expression \\
        --bam --no-bam-output \\
        --estimate-rspd --calc-ci --seed 12345 \\
        --num-thread --ci-memory 32768 \\
        [--paired-end] [--forward-prob 1.0] \\
        ${transcript-bam} ${index} ${output-prefix}

    """

    opt_runtime = utils.docmopt(dedent(main.__doc__))
    task = QuantRsemTask(
        output_dir=opt_runtime['--output-dir'],
        conf_path=opt_runtime['--conf']
    )

    opt = task.conf

    opt_ = {
        'sr': {'--paired-end': False},
        'pe': {'--paired-end': True}
    }
    opt.update(opt_[opt_runtime['--layout']])

    opt_ = {
        'fr': {'--forward-prob': 1.0},
        'rf': {'--forward-prob':  0.0},
        'none': {'--forward-prob': 0.5}
    }
    opt.update(opt_[opt_runtime['--strandness']])

    args = [None] * 3
    args[1] = opt_runtime['--index']

    bams = task.scattered(opt_runtime['--transcript-bam'])

    for b in bams:
        args[0] = b
        args[2] = task.output_prefix(b)

        cmd = "{base} {opt} {args}".format(
            base='rsem-calculate-expression',
            opt=utils.optdict_to_str(opt),
            args=' '.join(args)
        )

        sys.stderr.write("Command: {}\n".format(cmd))

        if not opt_runtime['--dry-run']:
            os.makedirs(task.output_subdir(b), exist_ok=True)
            proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            utils.puts_captured_output(proc)


if __name__ == '__main__':
    main()
