#! /usr/bin/env python3
#$ -S $HOME/.pyenv/shims/python3
#$ -l medium
#$ -l s_vmem=128G -l mem_req=128G
#$ -cwd
#$ -o ugelogs/
#$ -e ugelogs/

import sys
import os
import subprocess

import rnaseqde.utils as utils
from rnaseqde.task.base import CommandLineTask


class DeSleuthTask(CommandLineTask):
    instances = []

    @property
    def inputs(self):
        inputs_ = utils.dictupdate_if_exists(
            utils.docopt_keys(main.__doc__),
            self._inputs
        )

        inputs_.update({
            '--sample-sheet': self._inputs['<sample_sheet>'],
            '--output-dir': self.output_dir
            })

        return inputs_

    @property
    def outputs(self):
        outputs_ = self._inputs
        outputs_.update({
            f"--sleuth-{v}-result-{t}-tsv": os.path.join(self.output_dir, f"result_{v}_{t}.tsv") for v in ['gene', 'transcript'] for t in ['lrt', 'wt']
            })

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

    opt_runtime = utils.docmopt(main.__doc__)
    task = DeSleuthTask(output_dir=opt_runtime['--output-dir'])

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
        os.makedirs(task.output_dir, exist_ok=True)
        proc = subprocess.run(cmd, shell=True, capture_output=True)
        utils.puts_captured_output(proc, task.output_dir)


if __name__ == '__main__':
    main()
