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


class ConvSamToBamTask(CommandLineTask):
    instances = []
    in_array = True
    script = utils.actpath_to_sympath(__file__)

    @property
    def inputs(self):
        inputs_ = {'--output-dir': self.output_dir}

        binding = {
                '--dry-run': '--dry-run',
                '--sam': '--sam'
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
            utils.basename_replaced_ext('.sam', '.bam', input)
            )

        return output_

    @property
    def outputs(self):
        dict_ = super().inputs
        dict_['--bam'] = [self.output(input) for input in self.inputs['--sam']]

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

    task = ConvSamToBamTask()

    opt_runtime = utils.docmopt(dedent(main.__doc__))

    task.output_dir = opt_runtime['--output-dir']

    opt = opt_runtime

    sams = task.scattered(opt['--sam'])

    for s in sams:
        cmd = "samtools sort -@ 8 {sam} -o {bam}".format(
            sam=s,
            bam=task.output(s)
            )

        sys.stderr.write("Command: {}\n".format(cmd))

        if not opt_runtime['--dry-run']:
            subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # TODO: Remove SAM file(s)
        # cmd = "rm {sam}".format(sam=s)

        # sys.stderr.write("Command: {}\n".format(cmd))

        # if not opt_runtime['--dry-run']:
        #     subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


if __name__ == '__main__':
    main()
