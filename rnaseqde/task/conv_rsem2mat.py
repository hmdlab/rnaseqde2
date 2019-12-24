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


class ConvRsemToMatrixTask(CommandLineTask):
    instances = []

    @property
    def inputs(self):
        inputs_ = {'--output-dir': self.output_dir}

        binding = {
                '--dry-run': '--dry-run',
                '--gene-tsv': '--gene-tsv',
                '--transcript-tsv': '--transcript-tsv'
                }

        inputs_ = utils.dictbind(inputs_, super().inputs, binding)

        return inputs_

    @property
    def outputs(self):
        dict_ = super().inputs

        for v in ['gene', 'transcript']:
            key_ = "--{}-mat-tsv".format(v)
            dict_[key_] = os.path.join(self.output_dir, v, 'count_matrix.tsv')

        return dict_


def main():
    """
    Wrapper for UGE: Generate count matrix using RSEM

    Usage:
        conv_rsem2ebseq_mat [options] --gene-tsv <PATH>... --transcript-tsv <PATH>...

    Options:
        --output-dir <PATH>         : Output directory [default: .]
        --dry-run                   : Dry-run [default: False]
        --gene-tsv <PATH>...        : Gene-level counts TSV file
        --transcript-tsv <PATH>...  : Transcript-level counts TSV file

    """

    task = ConvRsemToMatrixTask()

    opt_runtime = utils.docmopt(dedent(main.__doc__))

    task.output_dir = opt_runtime['--output-dir']

    for v in ['gene', 'transcript']:
        key_ = "--{}-tsv".format(v)
        args = opt_runtime[key_]

        if args is None:
            continue

        output_dir_ = os.path.join(task.output_dir, v)

        cmd = "{base} {args} >| {output}".format(
            base='rsem-generate-data-matrix',
            args=' '.join(args),
            output=os.path.join(output_dir_, 'count_matrix.tsv')
            )

        sys.stderr.write("Command: {}\n".format(cmd))

        if not opt_runtime['--dry-run']:
            os.makedirs(output_dir_, exist_ok=True)
            proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            utils.puts_captured_output(proc)


if __name__ == '__main__':
    main()
