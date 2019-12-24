#! /usr/bin/env python3
#$ -S $HOME/.pyenv/shims/python3
#$ -l s_vmem=8G -l mem_req=8G
#$ -cwd
#$ -o ugelogs/
#$ -e ugelogs/

import sys
import os
import subprocess
from textwrap import dedent

import rnaseqde.utils as utils
from rnaseqde.task.base import CommandLineTask


class ConvCuffdiffToRawTask(CommandLineTask):
    instances = []

    @property
    def inputs(self):
        inputs_ = {'--output-dir': self.output_dir}

        binding = {
                '--dry-run': '--dry-run'
                }

        inputs_ = utils.dictbind(inputs_, super().inputs, binding)

        opt_ = {
                '--input': os.path.dirname(super().inputs['--transcript-raw-tsv'])
            }

        inputs_.update(opt_)

        return inputs_

    @property
    def outputs(self):
        outputs_ = super().inputs

        for v in ['transcript', 'gene']:
            outputs_["--{}-mat-tsv".format(v)] = os.path.join(self.output_dir, "count_matrix_{}.tsv".format(v))

        return outputs_


def main():
    """
    Wrapper for UGE: Convert Cuffdiff result to raw count matrix

    Usage:
        conv_cuffdiff2raw [options] --input <PATH>

    Options:
        --output-dir <PATH>  : Output directory [default: .]
        --dry-run            : Dry-run [default: False]
        --input <PATH>       : Cuffdiff output directory

    """

    opt_runtime = utils.docmopt(dedent(main.__doc__))
    task = ConvCuffdiffToRawTask(output_dir=opt_runtime['--output-dir'])

    os.makedirs(task.output_dir, exist_ok=True)

    opt = utils.dictfilter(opt_runtime, include=['--output-dir', '--dry-run'])

    for k, v in {'transcript': 'isoforms.read_group_tracking', 'gene': 'genes.read_group_tracking'}.items():
        args = [os.path.join(opt_runtime['--input'], v)]

        cmd = "{base} {script} {opt} {args}".format(
            base='Rscript',
            script=utils.from_root('scripts/conv_cuffdiff2raw.R'),
            opt=utils.optdict_to_str(opt),
            args=' '.join(args)
        )

        sys.stderr.write("Command: {}\n".format(cmd))

        if not opt_runtime['--dry-run']:
            proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            utils.puts_captured_output(proc, task.output_dir)


if __name__ == '__main__':
    main()
