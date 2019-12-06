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

from logging import getLogger


logger = getLogger(__name__)


class ConvAny2RawTximportTask(CommandLineTask):
    instances = []
    script = utils.actpath_to_sympath(__file__)
    in_parallel = False

    @property
    def inputs(self):
        inputs_ = {'--output-dir': self.output_dir}

        def _opt(upper_class):
            n = upper_class.__class__.__name__

            if n == 'DeCuffdiffTask':
                # import pdb; pdb.set_trace()
                return {
                    '--type': 'cuffdiff',
                    '--input': upper_class.outputs['--transcript-raw-tsv']
                }

            if n == 'QuantKallistoTask':
                return {
                    '--type': 'kallisto',
                    '--input': upper_class.outputs['--h5']
                }

            if n == 'QuantRsemTask':
                return {
                    '--type': 'rsem',
                    '--input': upper_class.outputs['--gene-tsv']
                }

            if n == 'QuantStringtieTask':
                return {
                    '--type': 'stringtie',
                    '--input': upper_class.outputs['--ctab']
                }

        inputs_.update(_opt(self.upper()))

        return inputs_

    @property
    def outputs(self):
        outputs_ = super().inputs

        for v in ['transcript']:
            outputs_['--' + v + '-mat-tsv'] = os.path.join(self.output_dir, v, 'count_matrix.tsv')

        return outputs_


def main():
    """
    Wrapper for UGE: Convert quantified data to raw count using tximport

    Usage:
        conv_any2raw_tximport [options] --type <TYPE> --input <PATH>...

    Options:
        --type <TYPE>        : Input type (cuffdiff/kallisto/rsem/stringtie)
        --level <TYPE>       : Analysis level (gene/transcript) [default: transcript]
        --output-dir <PATH>  : Output directory [default: .]
        --dry-run            : Dry-run [default: False]
        --input <PATH>...    : Output(s) of quantifier

    """

    task = ConvAny2RawTximportTask()

    opt_runtime = utils.docmopt(dedent(main.__doc__))

    task.output_dir = opt_runtime['--output-dir']
    os.makedirs(task.output_dir, exist_ok=True)

    args = [None] * 4

    args[0] = opt_runtime['--output-dir']
    args[1] = opt_runtime['--type']
    args[2] = opt_runtime['--level']
    args[3] = ' '.join(opt_runtime['--input'])

    cmd = "{base} {script} {args}".format(
        base='Rscript',
        script=utils.from_root('scripts/conv_any2raw_tximport.R'),
        args=' '.join(args)
    )

    sys.stderr.write("Command: {}\n".format(cmd))

    if not opt_runtime['--dry-run']:
        subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


if __name__ == '__main__':
    main()
