#! /usr/bin/env python3
#$ -S $HOME/.pyenv/shims/python3
#$ -pe def_slot 4
#$ -l s_vmem=16G -l mem_req=16G
#$ -cwd
#$ -o ugelogs/
#$ -e ugelogs/

import sys
import os
import subprocess

import rnaseqde.utils as utils
from rnaseqde.task.base import ArrayTask


class QuantRsemTask(ArrayTask):
    instances = []

    @property
    def inputs(self):
        inputs_ = utils.dictupdate_if_exists(
            utils.docopt_keys(main.__doc__),
            self._inputs
        )

        inputs_.update({
            '--index': self._inputs['--rsem-index'],
            '--output-dir': self.output_dir
            })

        return inputs_

    def suboutput_dir(self, input):
        suboutput_dir_ = os.path.join(
            self.output_dir,
            os.path.basename(os.path.dirname(input))
            )
        return suboutput_dir_

    def suboutputs(self, input, prefix='quantified'):
        binding = {
            '--output-prefix': prefix,
            '--gene-tsv': f"{prefix}.genes.results",
            '--transcript-tsv': f"{prefix}.isoforms.results",
            '--stat': f"{prefix}.stat"
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
    Wrapper for UGE: Quantify transcript abundance using RSEM

    Usage:
        quant_rsem [options] --index <PATH> --transcript-bam <PATH>...

    Options
        --index <PATH>              : Reference index file
        --layout <TYPE>             : Library layout (sr/pe) [default: sr]
        --strandness <TYPE>         : Library strandness (none/rf/fr) [default: none]
        --output-dir <PATH>         : Output directory [default: .]
        --conf <PATH>               : Configuration file
        --dry-run                   : Dry-run [default: False]
        --transcript-bam <PATH>...  : BAM file mapped to Transcriptome

    """

    opt_runtime = utils.docmopt(main.__doc__)
    task = QuantRsemTask(
        output_dir=opt_runtime['--output-dir'],
        conf_path=opt_runtime['--conf']
    )

    opt = task.conf

    opt_ = {
        'sr': {'--paired-end': False},
        'pe': {'--paired-end': True}
    }
    opt.update(opt_[opt_runtime['--layout']])

    opt_ = {
        'fr': {'--forward-prob': 1.0},
        'rf': {'--forward-prob':  0.0},
        'none': {'--forward-prob': 0.5}
    }
    opt.update(opt_[opt_runtime['--strandness']])

    args = [None] * 3
    args[1] = opt_runtime['--index']

    bams = task.scattered(opt_runtime['--transcript-bam'])

    for b in bams:
        args[0] = b
        args[2] = task.suboutputs(b)['--output-prefix']

        cmd = "{base} {opt} {args}".format(
            base='rsem-calculate-expression',
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
