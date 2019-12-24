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


class ConvSamToBamTask(ArrayTask):
    instances = []

    @property
    def inputs(self):
        inputs_ = OrderedDict({'--output-dir': self.output_dir})

        include_ = ['--dry-run', '--sam']

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
        dict_ = super().inputs
        dict_['--bam'] = [os.path.join(
            self.output_subdir(input), utils.basename_replaced_ext('.sam', '.bam', input)
            ) for input in self.inputs['--sam']]

        return dict_


def main():
    """
    Wrapper for UGE: Convert SAM to BAM using samtools

    Usage:
        conv_sam2bam [options] --sam <PATH>...

    Options:
        --output-dir <PATH>  : Output directory [default: .]
        --dry-run            : Dry-run [default: False]
        --sam <PATH>...      : SAM file(s)

    """

    opt_runtime = utils.docmopt(dedent(main.__doc__))
    task = ConvSamToBamTask(output_dir=opt_runtime['--output-dir'])

    opt = opt_runtime

    sams = task.scattered(opt['--sam'])

    print(sams)

    for s in sams:
        cmd = "samtools sort -@ 8 {sam} -o {bam}".format(
            sam=s,
            bam=os.path.join(task.output_subdir(s), utils.basename_replaced_ext('.sam', '.bam', s))
            )

        sys.stderr.write("Command: {}\n".format(cmd))

        if not opt_runtime['--dry-run']:
            os.makedirs(task.output_subdir(s), exist_ok=True)
            proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            utils.puts_captured_output(proc, task.output_subdir(s))

        # NOTE: Remove SAM file(s)
        # cmd = "rm {sam}".format(sam=s)

        # sys.stderr.write("Command: {}\n".format(cmd))

        # if not opt_runtime['--dry-run']:
        #     subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


if __name__ == '__main__':
    main()
