#! /usr/bin/env python3
#$ -S $HOME/.pyenv/shims/python3
#$ -l s_vmem=32G -l mem_req=32G
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


class DeSleuthTask(CommandLineTask):
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
                '--h5': '--h5'
                }

        inputs_ = utils.dictbind(inputs_, super().inputs, binding)

        return inputs_

    @property
    def outputs(self):
        outputs_ = super().inputs
        outputs_['--transcript-tsv'] = os.path.join(self.output_dir, 'results.tsv')

        return outputs_


def main():
    """
    Wrapper for UGE: Perform DE analysis using Sleuth

    Usage:
        de_sleuth [options] --gtf <PATH> --sample-sheet <PATH> --h5 <PATH>...

    Options:
        --gtf <PATH>           : GTF annotation file
        --output-dir <PATH>    : Output directory [default: .]
        --sample-sheet <PATH>  : Sample sheet
        --conf <PATH>          : Configuration file
        --dry-run              : Dry-run [default: False]
        --h5 <PATH>...         : kallisto h5 file(s)

    """

    task = DeSleuthTask()

    opt_runtime = utils.docmopt(dedent(main.__doc__))
    task.output_dir = opt_runtime['--output-dir']

    os.makedirs(task.output_dir, exist_ok=True)

    opt = utils.dictfilter(opt_runtime, ['--gtf', '--sample-sheet', '--output-dir'])
    args = [' '.join(opt_runtime['--h5'])]

    cmd = "{base} {script} {opt} {args}".format(
        base='Rscript',
        script=utils.from_root('scripts/de_sleuth.R'),
        opt=utils.optdict_to_str(opt),
        args=' '.join(args)
        )

    sys.stderr.write("Command: {}\n".format(cmd))

    if not opt_runtime['--dry-run']:
        proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        utils.write_proc_log(proc, task.output_dir)


if __name__ == '__main__':
    main()
