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
from collections import OrderedDict

import rnaseqde.utils as utils
from rnaseqde.task.base import ArrayTask


class QuantStringtieTask(ArrayTask):
    instances = []

    @property
    def inputs(self):
        inputs_ = OrderedDict({'--output-dir': self.output_dir})

        include_ = ['--gtf', '--strandness', '--dry-run', '--bam']

        inputs_.update(utils.dictfilter(super().inputs, include_))

        return inputs_

    def output_subdir(self, input):
        subdir_ = os.path.join(
            self.output_dir,
            os.path.basename(os.path.dirname(input))
        )

        return subdir_

    @property
    def outputs(self):
        outputs_ = super().inputs
        for k, v in [
            ('--quantified-gtf', 'quantified.gtf'),
            ('--ctab', 't_data.ctab')
        ]:
            outputs_[k] = [os.path.join(self.output_subdir(input), v) for input in self.inputs['--bam']]

        return outputs_


def main():
    """
    Wrapper for UGE: Quantify gene/transcript abundance using StringTie

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

    opt_runtime = utils.docmopt(dedent(main.__doc__))
    task = QuantStringtieTask(
        output_dir=opt_runtime['--output-dir'],
        conf_path=opt_runtime['--conf']
    )

    binding = {
        '-G': '--gtf'
    }

    opt = utils.dictbind(task.conf, opt_runtime, binding)

    opt_ = {
        'fr': {'--fr': True},
        'rf': {'--rf': True},
        'none': {}
    }
    opt.update(opt_[opt_runtime['--strandness']])

    args = [None]

    bams = task.scattered(opt_runtime['--bam'])
    for b in bams:
        opt['-o'] = os.path.join(task.output_subdir(b), 'quantified.gtf')
        args[0] = b

        cmd = "{base} {opt} {args}".format(
            base='stringtie',
            opt=utils.optdict_to_str(opt),
            args=' '.join(args)
            )

        sys.stderr.write("Command: {}\n".format(cmd))

        if not opt_runtime['--dry-run']:
            os.makedirs(task.output_subdir(b), exist_ok=True)
            proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            utils.puts_captured_output(proc, task.output_subdir(b))


if __name__ == '__main__':
    main()
