#! /usr/bin/env python3
#$ -S $HOME/.pyenv/shims/python3
#$ -l s_vmem=16G -l mem_req=16G
#$ -cwd
#$ -o ugelogs/
#$ -e ugelogs/

import sys
import os
import subprocess
from textwrap import dedent

import rnaseqde.utils as utils
from rnaseqde.task.base import ArrayTask


class QuantKallistoTask(ArrayTask):
    instances = []

    @property
    def inputs(self):
        inputs_ = {'--output-dir': self.output_dir}

        binding = {
                '--index': '--kallisto-index',
                '--gtf': '--gtf',
                '--layout': '--layout',
                '--strandness': '--strandness',
                '--sample': '--sample',
                '--dry-run': '--dry-run',
                '--fastq': '--fastq'
                }

        inputs_ = utils.dictbind(inputs_, super().inputs, binding)

        return inputs_

    def output_subdir(self, input, ext='.fastq.gz'):
        subdir_ = os.path.join(
            self.output_dir,
            utils.basename_replaced_ext(ext, '', input)
            )

        return subdir_

    @property
    def outputs(self):
        outputs_ = super().inputs
        if self.inputs['--layout'] == 'sr':
            fastq1s = self.inputs['--fastq']
        else:
            fastq1s = self.inputs['--fastq'][0::2]

        samples = self.inputs['--sample'] if self.inputs['--sample'] else fastq1s

        for k, v in {
            '--tsv': 'abundance.tsv',
            '--h5': 'abundance.h5',
            '--json': 'run_info.json'
        }.items():
            outputs_[k] = [os.path.join(self.output_subdir(s), v) for s in samples]

        return outputs_

    @property
    def n_tasks(self):
        if self.inputs['--layout'] == 'pe':
            return int(self._n_tasks() / 2)

        return self._n_tasks()


def main():
    """
    Wrapper for UGE: Quantify transcript abundance using Kallisto

    Usage:
        quant_kallisto [options] --index <PATH> [--sample <STR>...] --fastq <PATH>...

    Options:
        --index <PATH>       : Reference index file
        --gtf <PATH>         : GTF annotation file
        --layout <TYPE>      : Library layout (sr/pe) [default: sr]
        --strandness <TYPE>  : Library strandness (none/rf/fr) [default: none]
        --output-dir <PATH>  : Output directory [default: .]
        --sample <STR>...    : (Comma delimited) sample(s)
        --conf <PATH>        : Configuration file
        --dry-run            : Dry-run [default: False]
        --fastq <PATH>...    : (Ordered) FASTQ file(s)

    """

    opt_runtime = utils.docmopt(dedent(main.__doc__))
    task = QuantKallistoTask(
        output_dir=opt_runtime['--output-dir'],
        conf_path=opt_runtime['--conf']
    )

    if opt_runtime['--layout'] == 'sr':
        fastq1s = task.scattered(opt_runtime['--fastq'])
        fastq2s = [''] * len(opt_runtime['--fastq'])
    else:
        fastq1s = task.scattered(opt_runtime['--fastq'][0::2])
        fastq2s = task.scattered(opt_runtime['--fastq'][1::2])

    if opt_runtime['--sample']:
        samples = task.scattered(opt_runtime['--sample'])
    else:
        samples = fastq1s

    if len(samples) != len(fastq1s):
        raise Exception(
            "Invalid sample argument specified {} vs {}".format(len(samples), len(fastq1s))
        )

    binding = {
        '-i': '--index',
        '-g': '--gtf'
    }

    opt = utils.dictbind(task.conf, opt_runtime, binding)

    opt_ = {
        'sr': {
            '--single': True,
            '--fragment-length': 200.0,
            '--sd': 40.0
            },
        'pe': {}
    }
    opt.update(opt_[opt_runtime['--layout']])

    opt_ = {
        'fr': {'--fr-stranded': True},
        'rf': {'--rf-stranded':  True},
        'none': {}
    }
    opt.update(opt_[opt_runtime['--strandness']])

    for f1, f2, s in zip(fastq1s, fastq2s, samples):
        opt['-o'] = task.output_subdir(s)

        if f2 == '':
            args = [f1]
        else:
            args = [f1, f2]

        cmd = "{base} {opt} {args}".format(
            base='kallisto quant',
            opt=utils.optdict_to_str(opt),
            args=' '.join(args)
        )

        sys.stderr.write("Command: {}\n".format(cmd))

        if not opt_runtime['--dry-run']:
            os.makedirs(task.output_subdir(s), exist_ok=True)
            proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            utils.puts_captured_output(proc, task.output_subdir(s))


if __name__ == '__main__':
    main()
