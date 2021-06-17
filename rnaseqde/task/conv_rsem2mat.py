#! /usr/bin/env python3
#$ -S $HOME/.pyenv/shims/python3
#$ -cwd
#$ -o ugelogs/
#$ -e ugelogs/

import sys
import os
import subprocess

import rnaseqde.utils as utils
from rnaseqde.task.base import CommandLineTask


class ConvRsemToMatrixTask(CommandLineTask):
    instances = []

    @property
    def inputs(self):
        inputs_ = utils.dictupdate_if_exists(
            utils.docopt_keys(main.__doc__),
            self._inputs
        )

        inputs_.update({
            '--output-dir': self.output_dir
            })

        return inputs_

    @property
    def outputs(self):
        outputs_ = self._inputs
        outputs_.update({
            f"--{v}-mat-tsv": os.path.join(self.output_dir, v, 'count_matrix.tsv') for v in ['gene', 'transcript']
            })

        return outputs_


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

    opt_runtime = utils.docmopt(main.__doc__)

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
        os.makedirs(output_dir_, exist_ok=True)

        if not opt_runtime['--dry-run']:
            proc = subprocess.run(cmd, shell=True, capture_output=True)
            utils.puts_captured_output(proc, output_dir_)


if __name__ == '__main__':
    main()
