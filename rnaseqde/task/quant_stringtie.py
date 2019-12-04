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


class QuantStringtieTask(CommandLineTask):
    instances = []
    in_array = True
    script = utils.actpath_to_sympath(__file__)

    @property
    def inputs(self):
        inputs_ = {'--output-dir': self.output_dir}

        binding = {
                '--gtf': '--gtf',
                '--strandness': '--strandness',
                '--dry-run': '--dry-run',
                '--bam': '--bam',
                }

        inputs_ = utils.dictbind(inputs_, super().inputs, binding)

        return inputs_

    def output_subdir(self, input):
        subdir_ = os.path.join(
            self.output_dir,
            os.path.basename(os.path.dirname(input))
        )

        return subdir_

    def output(self, input):
        os.makedirs(self.output_subdir(input), exist_ok=True)
        output_ = os.path.join(
            self.output_subdir(input),
            'quantified.gtf'
            )

        return output_

    @property
    def outputs(self):
        outputs_ = super().inputs
        for k, v in [
            ('--quantified-gtf', 'quantified.gtf'),
            ('--ctab', 't_data.ctab')
        ]:
            outputs_[k] = [os.path.join(os.path.dirname(self.output(input)), v) for input in self.inputs['--bam']]

        return outputs_


def main():
    """
    Wrapper for UGE: Quantificate expression using StringTie

    Usage:
        quant_stringtie [options] --gtf <PATH> --bam <PATH>...

    Options:
        --gtf <PATH>         : GTF annotation file
        --strandness <TYPE>  : Library strandness (none/rf/fr) [default: none]
        --output-dir <PATH>  : Output directory [default: .]
        --conf <PATH>        : Configuration file
        --dry-run            : Dry-run [default: False]
        --bam <PATH>...      : BAM file(s)

    """

    task = QuantStringtieTask()
    opt_runtime = utils.docmopt(dedent(main.__doc__))
    opt_static = utils.load_conf(opt_runtime['--conf']) if opt_runtime['--conf'] else task.conf

    task.output_dir = opt_runtime['--output-dir']

    binding = {
        '-G': '--gtf'
    }

    opt = utils.dictbind(opt_static, opt_runtime, binding)

    opt_ = {
        'fr': {'--fr': True},
        'rf': {'--rf': True},
        'none': {}
    }
    opt.update(opt_[opt_runtime['--strandness']])

    args = [None]

    bams = task.scattered(opt_runtime['--bam'])
    for b in bams:
        opt['-o'] = task.output(b)
        args[0] = b

        cmd = "{base} {opt} {args}".format(
            base='stringtie',
            opt=utils.optdict_to_str(opt),
            args=' '.join(args)
            )

        sys.stderr.write("Command: {}\n".format(cmd))

        if not opt_runtime['--dry-run']:
            proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            with open(os.path.join(task.output_subdir(b), 'stderr.log'), 'w') as f:
                f.write(proc.stderr.decode())

            with open(os.path.join(task.output_subdir(b), 'stdout.log'), 'w') as f:
                f.write(proc.stdout.decode())


if __name__ == '__main__':
    main()
