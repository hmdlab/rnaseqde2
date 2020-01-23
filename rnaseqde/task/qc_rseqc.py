#! /usr/bin/env python3
#$ -S $HOME/.pyenv/shims/python3
#$ -l s_vmem=32G -l mem_req=32G
#$ -cwd
#$ -o ugelogs/
#$ -e ugelogs/

import sys
import os
import subprocess

import rnaseqde.utils as utils
from rnaseqde.task.base import ArrayTask


class QcRseqcTask(ArrayTask):
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
            '--': os.path.join(
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
    Wrapper for UGE: Quality control for BAM using RSeQC

    Usage:
        qc_rseqc [options] --bam <PATH>...

    Options:
        --output-dir <PATH>  : Output directory [default: .]
        --dry-run            : Dry-run [default: False]
        --bam <PATH>...      : BAM file(s)

    """

    opt_runtime = utils.docmopt(main.__doc__)
    task = QcRseqcTask(output_dir=opt_runtime['--output-dir'])

    opt = opt_runtime

    bams = task.scattered(opt['--bam'])

    for b in bams:

        # TODO: Paste from shell script
        cmd = "samtools sort -@ 4 {sam} -o {bam} && rm {sam}".format(
            bam=b
        )

        sys.stderr.write("Command: {}\n".format(cmd))

        if not opt_runtime['--dry-run']:
            os.makedirs(task.suboutput_dir(s), exist_ok=True)
            proc = subprocess.run(cmd, shell=True, capture_output=True)
            utils.puts_captured_output(proc, task.suboutput_dir(s))


if __name__ == '__main__':
    main()
