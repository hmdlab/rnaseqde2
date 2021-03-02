#! /usr/bin/env python3
#$ -S $HOME/.pyenv/shims/python3
#$ -l s_vmem=16G -l mem_req=16G
#$ -cwd
#$ -o ugelogs/
#$ -e ugelogs/

import sys
import os
import subprocess
import itertools

import rnaseqde.utils as utils
from rnaseqde.task.base import CommandLineTask


class DeEdgerTask(CommandLineTask):
    instances = []

    def __init__(
            self,
            required_tasks=None,
            output_dir=None,
            conf_dir=None,
            level=None):
        super().__init__(required_tasks=required_tasks, output_dir=output_dir)
        self.level = level

    @property
    def inputs(self):
        inputs_ = {'--output-dir': self.output_dir}

        binding = {
                '--sample-sheet': '<sample_sheet>',
                '--dry-run': '--dry-run'
                }

        if self.level == 'gene':
            binding.update({
                '--count-mat-tsv': '--gene-mat-tsv'
            })

        if self.level == 'transcript':
            binding.update({
                '--count-mat-tsv': '--transcript-mat-tsv'
            })

        inputs_ = utils.dictbind(inputs_, self._inputs, binding)

        return inputs_

    @property
    def output_dir(self):
        if self.level is None:
            return super().output_dir

        return os.path.join(super().output_dir, self.level)

    @property
    def outputs(self):
        outputs_ = self._inputs
        groups_ = self._inputs['--group']
        group_ = sorted(set(groups_), key=groups_.index)
        combinations = list(itertools.combinations(group_, 2))

        binding = {
            "--edger-{}-cpm-tsv": 'expressions_cpm.tsv',
            "--edger-{}-combined-tsv": 'combined.tsv',
            "--edger-{}-summary": 'summary.tsv'
            }

        for key, val in binding.items():
            outputs_[key.format(self.level)] = os.path.join(self.output_dir, val)

        for c in combinations:
            basename = "result_{}_vs_{}.tsv".format(c[0], c[1])
            outputs_[f"--edger-{self.level}-result-tsv"] = os.path.join(self.output_dir, basename)

        return outputs_


def main():
    """
    Wrapper for UGE: Perform DE analysis using edgeR

    Usage:
        de_edger [options] --sample-sheet --count-mat-tsv

    Options:
        --sample-sheet <PATH>        : Sample sheet
        --output-dir <PATH>          : Output directory [default: .]
        --dry-run                    : Dry-run [default: False]
        --count-mat-tsv <PATH>       : Gene/transcrit-level count matrix file

    """

    opt_runtime = utils.docmopt(main.__doc__)
    task = DeEdgerTask(output_dir=opt_runtime['--output-dir'])

    opt = utils.dictfilter(opt_runtime, exclude=['--count-mat-tsv', '--dry-run'])

    args = [None] * 1
    args[0] = opt_runtime['--count-mat-tsv']

    opt['--output-dir'] = task.output_dir

    cmd = "{base} {script} {opt} {args}".format(
        base='Rscript',
        script=utils.from_root('scripts/de_edger.R'),
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
