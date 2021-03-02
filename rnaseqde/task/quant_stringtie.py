#! /usr/bin/env python3
#$ -S $HOME/.pyenv/shims/python3
#$ -l s_vmem=8G -l mem_req=8G
#$ -cwd
#$ -o ugelogs/
#$ -e ugelogs/

import sys
import os
import subprocess

import rnaseqde.utils as utils
from rnaseqde.task.base import ArrayTask


class QuantStringtieTask(ArrayTask):
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
        binding = {
            '--quantified-gtf': 'quantified.gtf',
            '--ctab': 't_data.ctab'
        }

        return self._suboutputs(input, binding)

    @property
    def outputs(self):
        outputs_ = self._inputs
        outputs_.update(
            utils.dictcombine([self.suboutputs(i) for i in self.incrementer])
        )

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

    opt_runtime = utils.docmopt(main.__doc__)
    task = QuantStringtieTask(
        output_dir=opt_runtime['--output-dir'],
        conf=opt_runtime['--conf']
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
        opt['-o'] = os.path.join(task.suboutput_dir(b), 'quantified.gtf')
        args[0] = b

        cmd = "{base} {opt} {args}".format(
            base='stringtie',
            opt=utils.optdict_to_str(opt),
            args=' '.join(args)
            )

        sys.stderr.write("Command: {}\n".format(cmd))

        if not opt_runtime['--dry-run']:
            os.makedirs(task.suboutput_dir(b), exist_ok=True)
            proc = subprocess.run(cmd, shell=True, capture_output=True)
            utils.puts_captured_output(proc, task.suboutput_dir(b))


if __name__ == '__main__':
    main()
