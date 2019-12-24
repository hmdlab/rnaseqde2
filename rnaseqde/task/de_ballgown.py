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


class DeBallgownTask(CommandLineTask):
    instances = []

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
            key_ = "--{}-tsv".format(v)
            outputs_[key_] = os.path.join(self.output_dir, v, 'results.tsv')

        return outputs_


def main():
    """
    Wrapper for UGE: Perform DE analysis using ballgown

    Usage:
        de_ballgown [options] [--gtf <PATH>] --sample-sheet <PATH> --ctab <PATH>...

    Options:
        --gtf <PATH>            : GTF annotation file
        --sample-sheet <PATH>   : Sample sheet
        --output-dir <PATH>     : Output directory [default: .]
        --dry-run               : Dry-run [default: False]
        --ctab <PATH>...        : Count tab delimited file(s)

    """

    opt_runtime = utils.docmopt(dedent(main.__doc__))
    task = DeBallgownTask(output_dir=opt_runtime['--output-dir'])

    opt = utils.dictfilter(opt_runtime, ['--output-dir', '--sample-sheet'])
    opt['--gtf'] = opt_runtime['--gtf'] if opt_runtime['--gtf'] else "'#'"
    args = [' '.join(opt_runtime['--ctab'])]

    cmd = "{base} {script} {opt} {args}".format(
        base='Rscript',
        script=utils.from_root('scripts/de_ballgown.R'),
        opt=utils.optdict_to_str(opt),
        args=' '.join(args)
        )

    sys.stderr.write("Command: {}\n".format(cmd))

    if not opt_runtime['--dry-run']:
        os.makedirs(task.output_dir, exist_ok=True)
        proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        utils.puts_captured_output(proc, task.output_dir)


if __name__ == '__main__':
    main()
