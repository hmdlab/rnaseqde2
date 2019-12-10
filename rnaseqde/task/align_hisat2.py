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
from textwrap import dedent

import rnaseqde.utils as utils
from rnaseqde.task.base import CommandLineTask

from logging import getLogger


logger = getLogger(__name__)


class AlignHisat2Task(CommandLineTask):
    instances = []
    in_array = True
    script = utils.actpath_to_sympath(__file__)

    @property
    def inputs(self):
        inputs_ = {'--output-dir': self.output_dir}

        binding = {
                '--index': '--hisat2-index',
                '--layout': '--layout',
                '--strandness': '--strandness',
                '--sample': '--sample',
                '--dry-run': '--dry-run',
                '--fastq': '--fastq'
                }

        inputs_ = utils.dictbind(inputs_, super().inputs, binding)

        return inputs_

    def output_subdir(self, input):
        subdir_ = os.path.join(
            self.output_dir,
            utils.basename_replaced_ext('.fastq.gz', '', input)
            )

        return subdir_

    def output(self, input):
        output_dir_ = self.output_subdir(input)
        os.makedirs(output_dir_, exist_ok=True)
        output_ = os.path.join(
            output_dir_,
            'aligned.sam')

        return output_

    @property
    def outputs(self):
        if self.inputs['--layout'] == 'sr':
            fastq1s = self.inputs['--fastq']
        else:
            fastq1s = self.inputs['--fastq'][0::2]

        samples = self.inputs['--sample'] if self.inputs['--sample'] else fastq1s

        outputs_ = super().inputs
        outputs_['--sam'] = [self.output(s) for s in samples]

        return outputs_

    @property
    # TBD: Should implement on the super class or not
    def _qsub_threads(self):
        d = 1 if self.inputs['--layout'] == 'sr' else 2
        n_tasks = len(self.inputs['--fastq']) / d
        step = 1
        return "1-{}:{}".format(str(int(n_tasks)), step)


def main():
    """
    Wrapper for UGE: Align reads to the reference genome using HISAT2

    Usage:
        align_hisat2 [options] --index <PATH> [--sample <STR>...] --fastq <PATH>...

    Options:
        --index <PATH>       : Reference index file
        --layout <TYPE>      : Library layout (sr/pe) [default: sr]
        --strandness <TYPE>  : Library strandness (none/rf/fr) [default: none]
        --output-dir <PATH>  : Output directory [default: .]
        --sample <STR>...    : (Comma delimited) sample(s)
        --conf <PATH>        : Configuration file
        --dry-run            : Dry-run [default: False]
        --fastq <PATH>...    : (Ordered) FASTQ file(s)

    """

    task = AlignHisat2Task()

    opt_runtime = utils.docmopt(dedent(main.__doc__))
    opt_static = utils.load_conf(opt_runtime['--conf']) if opt_runtime['--conf'] else task.conf

    task.output_dir = opt_runtime['--output-dir']

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
        '-x': '--index'
    }

    opt = utils.dictbind(opt_static, opt_runtime, binding)
    opt_ = {
        'fr': {'--rna-strandness': 'FR'},
        'rf': {'--rna-strandness':  'RF'},
        'none': {}
    }
    opt.update(opt_[opt_runtime['--strandness']])

    for f1, f2, s in zip(fastq1s, fastq2s, samples):
        if f2 == '':
            opt['-U'] = f1
        else:
            opt['-1'] = f1
            opt['-2'] = f2

        opt['-S'] = task.output(s)

        # NOTE: Output unaligned reads
        opt['--un-conc'] = task.output(s).replace('aligned.sam', 'unaligned.fastq')

        cmd = "{base} {opt}".format(
            base='hisat2',
            opt=utils.optdict_to_str(opt)
        )

        sys.stderr.write("Command: {}\n".format(cmd))

        if not opt_runtime['--dry-run']:
            proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            with open(os.path.join(task.output_subdir(s), 'stderr.log'), 'w') as f:
                f.write(proc.stderr.decode())

            with open(os.path.join(task.output_subdir(s), 'stdout.log'), 'w') as f:
                f.write(proc.stdout.decode())


if __name__ == '__main__':
    main()
