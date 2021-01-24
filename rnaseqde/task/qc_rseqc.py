#! /usr/bin/env python3
# $ -S $HOME/.pyenv/shims/python3
# $ -l s_vmem=32G -l mem_req=32G
# $ -cwd
# $ -o ugelogs/
# $ -e ugelogs/

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
            utils.docopt_keys(main.__doc__), self._inputs
        )

        inputs_.update({"--output-dir": self.output_dir})

        return inputs_

    def suboutput_dir(self, input):
        suboutput_dir_ = os.path.join(
            self.output_dir, os.path.basename(os.path.abspath(os.path.dirname(input)))
        )

        return suboutput_dir_

    def suboutputs(self, input):
        suboutputs_ = {
            "--": os.path.join(
                self.suboutput_dir(input),
                utils.basename_replaced_ext(".sam", ".bam", input),
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
        --output-dir <PATH>  : Output directory [default: qc_rseqc]
        --dry-run            : Dry-run [default: False]
        --gtf <PATH>         : GTF file
        --bam <PATH>...      : BAM file(s)

    """

    opt_runtime = utils.docmopt(main.__doc__)

    task = QcRseqcTask(output_dir=opt_runtime["--output-dir"])

    opt = opt_runtime

    gtf = opt["--gtf"]
    bams = task.scattered(opt["--bam"])

    bed = os.path.join(
        os.path.dirname(gtf), utils.basename_replaced_ext(".gtf", ".bed", gtf)
    )

    if not os.path.exists(bed):
        cmd1 = "{script} --tx-only {gtf}".format(
            script=utils.from_root("scripts/gtf2bed4igv.py"), gtf=gtf
        )

        sys.stderr.write("Command: {}\n".format(cmd1))

        if not opt_runtime["--dry-run"]:
            proc = subprocess.run(cmd1, shell=True, capture_output=False)

    for b in bams:
        cmd2 = "{script} --bed {bed} --output-dir {output_dir} {bam}".format(
            script=utils.from_root("scripts/qc_rseqc.sh"),
            output_dir=task.output_dir,
            bed=bed,
            bam=utils.actpath_to_sympath(os.path.abspath(b)),
        )

        sys.stderr.write("Command: {}\n".format(cmd2))

        if not opt_runtime["--dry-run"]:
            os.makedirs(task.output_dir, exist_ok=True)
            proc = subprocess.run(cmd2, shell=True, capture_output=True)
            utils.puts_captured_output(proc, task.output_dir)


if __name__ == "__main__":
    main()
