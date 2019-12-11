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

    """

    task = DeEbseqTask()
    opt_runtime = utils.docmopt(dedent(main.__doc__))

    task.output_dir = opt_runtime['--output-dir']

    # NOTE: Input matrix MUST ordered by group
    n_reps = [str(v) for v in collections.Counter(opt_runtime['--group']).values()]

    for v in ['gene', 'transcript']:
        opt = {}
        output_dir_ = os.path.join(task.output_dir, v)
        os.makedirs(output_dir_, exist_ok=True)

        key_ = "--{}-mat-tsv".format(v)

        args = [None] * 3
        ngvector = "'#'" if v == 'gene' else opt_runtime['--ngvector']

        opt['--ngvector'] = ngvector
        opt['--level'] = v
        opt['--output-dir'] = output_dir_

        args[0] = opt_runtime[key_]
        args[1], args[2] = n_reps

        if None in args:
            for i, _ in enumerate(args):
                if _ is None:
                    raise Exception("Positional arg{} is not assigned.".format(i))

        cmd = "{base} {script} {opt} {args}".format(
            base='Rscript',
            script=utils.from_root('scripts/rsem-for-ebseq-find-DE.R'),
            opt=utils.optdict_to_str(opt),
            args=' '.join(args)
            )

        sys.stderr.write("Command: {}\n".format(cmd))

        if not opt_runtime['--dry-run']:
            proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            utils.write_proc_log(proc, output_dir_, stdout=True)


if __name__ == '__main__':
    main()
