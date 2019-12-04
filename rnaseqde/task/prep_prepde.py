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

from logging import getLogger


logger = getLogger(__name__)


class PrepPrepdeTask(CommandLineTask):
    instances = []
    in_array = False
    script = utils.actpath_to_sympath(__file__)

    @property
    def inputs(self):
        inputs_ = {'--output-dir': self.output_dir}

        binding = {
                '--sample': '--sample',
                '--dry-run': '--dry-run',
                '--quantified-gtf': '--quantified-gtf'
                }

        inputs_ = utils.dictbind(inputs_, super().inputs, binding)

        return inputs_

    @property
    def outputs(self):
        outputs_ = super().inputs

        for level in ['gene', 'transcript']:
            outputs_['--' + level + '-csv'] = os.path.join(
                self.output_dir,
                "{}_count_matrix.csv".format(level)
                )

        return outputs_

    def puts_list_targets(self, inputs, samples):
        targets = [os.path.abspath(input) for input in inputs]
        list_targets = os.path.join(self.output_dir, 'list_targets.txt')
        body = ['\t'.join([name, path]) for name, path in zip(samples, targets)]

        with open(list_targets, 'w+') as f:
            f.write('\n'.join(body))

        return list_targets


def main():
    """
    Wrapper for UGE: Generate count matrix using PrepDE.py

    Usage:
        quant_stringtie [options] --sample <STR>... --quantified-gtf <PATH>...

    Options:
        --sample <STR>...           : Sample(s)
        --output-dir <PATH>         : Output directory [default: .]
        --dry-run                   : Dry-run [default: False]
        --quantified-gtf <PATH>...  : Quantified GTF file(s)

    """

    task = PrepPrepdeTask()
    opt_runtime = utils.docmopt(dedent(main.__doc__))

    task.output_dir = opt_runtime['--output-dir']

    os.makedirs(task.output_dir, exist_ok=True)
    list_targets = task.puts_list_targets(
        opt_runtime['--quantified-gtf'],
        opt_runtime['--sample']
        )

    opt = {
        '-i': list_targets,
        '-g': task.outputs['--gene-csv'],
        '-t': task.outputs['--transcript-csv']
    }

    cmd = "{base} {opt}".format(
        base='prepDE.py',
        opt=utils.optdict_to_str(opt)
        )

    sys.stderr.write("Command: {}\n".format(cmd))

    if not opt_runtime['--dry-run']:
        subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


if __name__ == '__main__':
    main()
