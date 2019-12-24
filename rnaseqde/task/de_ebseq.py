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


class DeEbseqTask(CommandLineTask):
    instances = []

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
        for v in ['gene', 'transcript']:
            key_ = "--{}-tsv".format(v)
            outputs_[key_] = os.path.join(self.output_dir, v, 'results.tsv')

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
        key_ = "--{}-mat-tsv".format(v)
        if opt_runtime[key_] is None:
            continue

        output_dir_ = os.path.join(task.output_dir, v)

        opt = {
            '--ngvector': "'#'" if v == 'gene' else opt_runtime['--ngvector'],
            '--level': v,
            '--output-dir': output_dir_
        }

        args = [None] * 3
        args[0] = opt_runtime[key_]
        args[1], args[2] = n_reps

        cmd = "{base} {script} {opt} {args}".format(
            base='Rscript',
            script=utils.from_root('scripts/de_ebseq.R'),
            opt=utils.optdict_to_str(opt),
            args=' '.join(args)
            )

        sys.stderr.write("Command: {}\n".format(cmd))

        if not opt_runtime['--dry-run']:
            os.makedirs(output_dir_, exist_ok=True)
            proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            utils.puts_captured_output(proc)

if __name__ == '__main__':
    main()
