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


class DeBallgownTask(CommandLineTask):
    instances = []
    in_array = False
    script = utils.actpath_to_sympath(__file__)

    @property
    def inputs(self):
        inputs_ = {'--output-dir': self.output_dir}

        binding = {
                '--gtf': '--gtf',
                '--sample-sheet': '<sample_sheet>',
                '--dry-run': '--dry-run',
                '--ctab': '--ctab'
                }

        if self.upper().__class__.__name__ == 'QuantStringtieTask':
            del binding['--gtf']

        inputs_ = utils.dictbind(inputs_, super().inputs, binding)

        return inputs_

    @property
    def outputs(self):
        outputs_ = super().inputs

        for v in ['gene', 'transcript']:
            outputs_['--' + v + '-tsv'] = os.path.join(self.output_dir, v, '_results.tsv')
            outputs_['--' + v + '-de-tsv'] = os.path.join(self.output_dir, v, '_results_de.tsv')

        return outputs_


def main():
    """
    Wrapper for UGE: Perform DE analysis using ballgown

    Usage:
        de_ballgown [options] [--gtf <PATH>] --sample-sheet <PATH> --ctab <PATH>...

    Options:
        --gtf <PATH>            : GTF annotation file
        --output-dir <PATH>     : Output directory [default: .]
        --dry-run               : Dry-run [default: False]
        --sample-sheet <PATH>   : Sample sheet
        --ctab <PATH>...        : Count tab delimited file(s)

    """

    task = DeBallgownTask()

    opt_runtime = utils.docmopt(dedent(main.__doc__))
    task.output_dir = opt_runtime['--output-dir']
    os.makedirs(task.output_dir, exist_ok=True)

    opt = opt_runtime

    args = [None] * 4
    args[0] = opt['--output-dir']
    args[1] = opt['--sample-sheet']
    args[2] = opt['--gtf'] if opt['--gtf'] else "'#'"
    args[3] = ' '.join(opt['--ctab'])

    cmd = "{base} {script} {args}".format(
        base='Rscript',
        script=utils.from_root('scripts/de_ballgown.R'),
        args=' '.join(args)
        )

    sys.stderr.write("Command: {}\n".format(cmd))

    if not opt_runtime['--dry-run']:
        subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


if __name__ == '__main__':
    main()
