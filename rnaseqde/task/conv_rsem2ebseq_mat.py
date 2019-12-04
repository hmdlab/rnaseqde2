#! /usr/bin/env python3
#$ -S $HOME/.pyenv/shims/python3
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


class ConvRsemToEbseqMatrixTask(CommandLineTask):
    instances = []
    in_array = False
    script = utils.actpath_to_sympath(__file__)

    @property
    def inputs(self):
        inputs_ = {'--output-dir': self.output_dir}

        binding = {
                '--gene-tsv': '--gene-tsv',
                '--transcript-tsv': '--transcript-tsv'
                }

        inputs_ = utils.dictbind(inputs_, super().inputs, binding)

        return inputs_

    def output_subdir(self, unit):
        return os.path.join(self.output_dir, unit)

    def output(self, unit):
        return os.path.join(self.output_subdir(unit), 'count_matrix.tsv')

    @property
    def outputs(self):
        dict_ = super().inputs

        for u in ['gene', 'transcript']:
            key_ = "--{}-mat-tsv".format(u)
            dict_[key_] = self.output(u)

        return dict_


def main():
    """
    Wrapper for UGE: Generate count matrix using RSEM

    Usage:
        conv_rsem2ebseq_mat [options] --gene-tsv <PATH>... --transcript-tsv <PATH>...

    Options:
        --gene-tsv <PATH>...        : Gene-level counts TSV file
        --transcript-tsv <PATH>...  : Transcript-level counts TSV file
        --output-dir <PATH>         : Output directory [default: .]
        --dry-run                   : Dry-run [default: False]

    Example:
        rsem-generate-data-matrix [<rsem-result-tsv>...]

    """

    task = ConvRsemToEbseqMatrixTask()

    opt_runtime = utils.docmopt(dedent(main.__doc__))

    task.output_dir = opt_runtime['--output-dir']

    for level in ['gene', 'transcript']:
        os.makedirs(task.output_subdir(level), exist_ok=True)

        key_ = "--{}-tsv".format(level)
        args = opt_runtime[key_]

        cmd = "{base} {args} >| {output}".format(
            base='rsem-generate-data-matrix',
            args=' '.join(args),
            output=task.output(level)
            )

        sys.stderr.write("Command: {}\n".format(cmd))

        if not opt_runtime['--dry-run']:
            proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


if __name__ == '__main__':
    main()
