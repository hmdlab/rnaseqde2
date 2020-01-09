#! /usr/bin/env python3
#$ -S $HOME/.pyenv/shims/python3
#$ -l s_vmem=8G -l mem_req=8G
#$ -cwd
#$ -o ugelogs/
#$ -e ugelogs/

import sys
import os
import subprocess

import rnaseqde.utils as utils
from rnaseqde.task.base import CommandLineTask


class ConvCuffdiffToRawTask(CommandLineTask):
    instances = []

    @property
    def inputs(self):
        inputs_ = utils.dictupdate_if_exists(
            utils.docopt_keys(main.__doc__),
            self._inputs
        )

        inputs_.update({
            '--input': os.path.dirname(self._inputs['--transcript-raw-tsv']),
            '--output-dir': self.output_dir
            })

        return inputs_

    @property
    def outputs(self):
        outputs_ = self._inputs
        outputs_.update({
            f"--{v}-mat-tsv": os.path.join(self.output_dir, f"count_matrix_{v}.tsv") for v in ['gene', 'transcript']
            })

        return outputs_


def main():
    """
    Wrapper for UGE: Convert Cuffdiff result to raw count matrix

    Usage:
        conv_cuffdiff2raw [options] --input <PATH>

    Options:
        --output-dir <PATH>  : Output directory [default: .]
        --dry-run            : Dry-run [default: False]
        --input <PATH>       : Cuffdiff output directory

    """

    opt_runtime = utils.docmopt(main.__doc__)
    task = ConvCuffdiffToRawTask(output_dir=opt_runtime['--output-dir'])

    opt = utils.dictfilter(opt_runtime, include=['--output-dir', '--dry-run'])

    for k, v in {'transcript': 'isoforms.read_group_tracking', 'gene': 'genes.read_group_tracking'}.items():
        args = [os.path.join(opt_runtime['--input'], v)]

        cmd = "{base} {script} {opt} {args}".format(
            base='Rscript',
            script=utils.from_root('scripts/conv_cuffdiff2raw.R'),
            opt=utils.optdict_to_str(opt),
            args=' '.join(args)
        )

        sys.stderr.write("Command: {}\n".format(cmd))

        if not opt_runtime['--dry-run']:
            os.makedirs(task.output_dir, exist_ok=True)
            proc = subprocess.run(cmd, shell=True, capture_output=True)
            utils.puts_captured_output(proc, task.output_dir)


if __name__ == '__main__':
    main()
