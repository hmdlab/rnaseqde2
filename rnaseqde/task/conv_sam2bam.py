#! /usr/bin/env python3
#$ -S $HOME/.pyenv/shims/python3
#$ -pe def_slot 4
#$ -l s_vmem=4G -l mem_req=4G
#$ -cwd
#$ -o ugelogs/
#$ -e ugelogs/

import sys
import os
import subprocess

import rnaseqde.utils as utils
from rnaseqde.task.base import ArrayTask


class ConvSamToBamTask(ArrayTask):
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

    def suboutput_dir(self, input):
        suboutput_dir_ = os.path.join(
            self.output_dir,
            os.path.basename(os.path.dirname(input))
            )

        return suboutput_dir_

    def suboutputs(self, input):
        suboutputs_ = {
            '--bam': os.path.join(
                self.suboutput_dir(input),
                utils.basename_replaced_ext('.sam', '.bam', input)
            )
        }

        return suboutputs_

    @property
    def outputs(self):
        outputs_ = self._inputs
        outputs_.update(
            utils.dictcombine([self.suboutputs(i) for i in self.incrementer])
        )

        return outputs_


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

    opt_runtime = utils.docmopt(main.__doc__)
    task = ConvSamToBamTask(output_dir=opt_runtime['--output-dir'])

    opt = opt_runtime

    sams = task.scattered(opt['--sam'])

    for s in sams:
        cmd = "samtools sort -@ 4 {sam} -o {bam} && rm {sam}".format(
            sam=s,
            bam=task.suboutputs(s)['--bam']
        )

        sys.stderr.write("Command: {}\n".format(cmd))

        if not opt_runtime['--dry-run']:
            os.makedirs(task.suboutput_dir(s), exist_ok=True)
            proc = subprocess.run(cmd, shell=True, capture_output=True)
            utils.puts_captured_output(proc, task.suboutput_dir(s))


if __name__ == '__main__':
    main()
