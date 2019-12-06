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


class DeEdgerTask(CommandLineTask):
    instances = []
    in_array = False
    script = utils.actpath_to_sympath(__file__)

    @property
    def inputs(self):
        inputs_ = {'--output-dir': self.output_dir}

        binding = {
                '--sample-sheet': '<sample_sheet>',
                '--dry-run': '--dry-run',
                '--count-mat-tsv': '--transcript-mat-tsv'
                }

        inputs_ = utils.dictbind(inputs_, super().inputs, binding)

        return inputs_

    @property
    def outputs(self):
        outputs_ = super().inputs

        # TODO: Append gene-level analysis
        for v in ['transcript']:
            outputs_['--' + v + '-tsv'] = os.path.join(self.output_dir, v, '_results.tsv')
            outputs_['--' + v + '-de-tsv'] = os.path.join(self.output_dir, v, '_results_de.tsv')

        return outputs_



def main():
    """
    Wrapper for UGE: Perform DE analysis using edgeR

    Usage:
        de_edger [options] --sample-sheet --count-mat-tsv

    Options:
        --sample-sheet <PATH>        : Sample sheet
        --output-dir <PATH>          : Output directory [default: .]
        --dry-run                    : Dry-run [default: False]
        --count-mat-tsv <PATH>  : Transcrit-level count matrix file

    """

    task = DeEdgerTask()
    opt_runtime = utils.docmopt(dedent(main.__doc__))

    task.output_dir = opt_runtime['--output-dir']

    # TODO: Append gene-level analysis
    for v in ['transcript']:
        output_dir_ = os.path.join(task.output_dir, v)
        os.makedirs(output_dir_, exist_ok=True)

        args = [None] * 3

        args[0] = opt_runtime['--sample-sheet']
        args[1] = opt_runtime['--output-dir']
        args[2] = opt_runtime['--count-mat-tsv']

        cmd = "{base} {script} {args}".format(
            base='Rscript',
            script=utils.from_root('scripts/de_edger.R'),
            args=' '.join(args)
        )

    sys.stderr.write("Command: {}\n".format(cmd))

    if not opt_runtime['--dry-run']:
        subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


if __name__ == '__main__':
    main()
