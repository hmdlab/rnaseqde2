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
from rnaseqde.task.base import CommandLineTask


class ConvAnyToRawTask(CommandLineTask):
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

        def _opt(upper_class):
            n = upper_class.__class__.__name__

            if n == 'QuantKallistoTask':
                return {
                    '--type': 'kallisto',
                    '--input': upper_class.outputs['--h5']
                }

            if n == 'QuantRsemTask':
                return {
                    '--type': 'rsem',
                    '--input': upper_class.outputs['--transcript-tsv']
                }

            if n == 'QuantStringtieTask':
                return {
                    '--type': 'stringtie',
                    '--input': upper_class.outputs['--ctab']
                }

            if n == 'QuantSalmonTask':
                return {
                    '--type': 'salmon',
                    '--input': upper_class.outputs['--sf']
                }

        inputs_.update(_opt(self.upper()))

        return inputs_

    @property
    def outputs(self):
        outputs_ = self._inputs
        outputs_.update({
            f"--{v}-mat-tsv": os.path.join(self.output_dir, f"count_matrix_{v}.tsv") for v in ['gene', 'transcript']
            })

        return outputs_


def main():
    """
    Wrapper for UGE: Convert quantified data to raw count using tximport

    Usage:
        conv_any2raw_tximport [options] --gtf <PATH> --type <TYPE> --input <PATH>...

    Options:
        --gtf <PATH>         : GTF annotation file
        --type <TYPE>        : Input type (kallisto/rsem/stringtie/salmon)
        --output-dir <PATH>  : Output directory [default: .]
        --dry-run            : Dry-run [default: False]
        --input <PATH>...    : Output(s) of quantifier;
                               kallisto: abundance.h5, RSEM: quantified.isoforms.results, StringTie: t_data.ctab, Salmon: quant.sf

    """

    opt_runtime = utils.docmopt(main.__doc__)
    task = ConvAnyToRawTask(output_dir=opt_runtime['--output-dir'])

    opt = utils.dictfilter(opt_runtime, ['--gtf', '--type', '--output-dir'])
    args = [' '.join(opt_runtime['--input'])]

    cmd = "{base} {script} {opt} {args}".format(
        base='Rscript',
        script=utils.from_root('scripts/conv_any2raw.R'),
        opt=utils.optdict_to_str(opt),
        args=' '.join(args)
    )

    sys.stderr.write("Command: {}\n".format(cmd))

    if not opt_runtime['--dry-run']:
        os.makedirs(task.output_dir, exist_ok=True)
        proc = subprocess.run(cmd, shell=True, capture_output=True)
        utils.puts_captured_output(proc, task.output_dir)


if __name__ == '__main__':
    main()
