#! /usr/bin/env python3
#$ -S $HOME/.pyenv/shims/python3
#$ -cwd
#$ -o ugelogs/
#$ -e ugelogs/

import sys
import os
import subprocess
import collections
from textwrap import dedent

import rnaseqde.utils as utils
from rnaseqde.task.base import CommandLineTask

from logging import getLogger


logger = getLogger(__name__)


class DeEbseqTask(CommandLineTask):
    instances = []
    in_array = False
    script = utils.actpath_to_sympath(__file__)

    @property
    def inputs(self):
        inputs_ = {'--output-dir': self.output_dir}

        binding = {
                '--ngvector': '--ebseq-ngvector',
                '--group': '--group',
                '--dry-run': '--dry-run',
                '--gene-mat-tsv': '--gene-mat-tsv',
                '--transcript-mat-tsv': '--transcript-mat-tsv'
                }

        inputs_ = utils.dictbind(inputs_, super().inputs, binding)

        return inputs_

    @property
    def outputs(self):
        outputs_ = super().inputs
        for level in ['gene', 'transcript']:
            outputs_[level + '-tsv'] = os.path.join(self.output_dir, level, 'results.tsv')

        return outputs_


def main():
    """
    Wrapper for UGE: Perform DE analysis using EBSeq

    Usage:
        de_ebseq [options] --ngvector <PATH> --group <STR>... --gene-mat-tsv <PATH> --transcript-mat-tsv <PATH>

    Options:
        --ngvector <PATH>            : NgVector file
        --group <STR>...             : (Comma delimited) group(s)
        --output-dir <PATH>          : Output directory [default: .]
        --dry-run                    : Dry-run [default: False]
        --gene-mat-tsv <PATH>        : Gene-level count matrix file
        --transcript-mat-tsv <PATH>  : Transcrit-level count matrix file

    Example:
        Rscript scripts/rsem-for-ebseq-find-DE.R <path_to_ebseq_lib> [ngvec] <gene-transcript-matrix> <output_prefix> [<conditions>...]

    """

    task = DeEbseqTask()
    opt_runtime = utils.docmopt(dedent(main.__doc__))

    task.output_dir = opt_runtime['--output-dir']

    # NOTE: Input matrix MUST ordered by group
    n_reps = [str(v) for v in collections.Counter(opt_runtime['--group']).values()]

    os.makedirs(task.output_dir, exist_ok=True)

    for level in ['gene', 'transcript']:
        output_dir_ = os.path.join(task.output_dir, level)
        os.makedirs(output_dir_, exist_ok=True)

        key_ = "--{}-mat-tsv".format(level)

        args = [None] * 5
        ngvector = "'#'" if level == 'gene' else opt_runtime['--ngvector']

        args[0] = '.'
        args[1] = ngvector
        args[2] = opt_runtime[key_]
        args[3] = os.path.join(output_dir_, 'results.tsv')
        args[4] = ' '.join(n_reps)

        if None in args:
            for i, _ in enumerate(args):
                if _ is None:
                    raise Exception("Positional arg{} is not assigned.".format(i))

        cmd = "{base} {script} {args}".format(
            base='Rscript',
            script=utils.from_root('scripts/rsem-for-ebseq-find-DE.R'),
            args=' '.join(args)
            )

        sys.stderr.write("Command: {}\n".format(cmd))

        if not opt_runtime['--dry-run']:
            subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


if __name__ == '__main__':
    main()
