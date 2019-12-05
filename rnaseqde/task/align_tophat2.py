#! /usr/bin/env python3
#$ -S $HOME/.pyenv/shims/python3
#$ -pe def_slot 8
#$ -l s_vmem=4G -l mem_req=4G
#$ -cwd
#$ -o ugelogs/
#$ -e ugelogs/

import sys
import os
import subprocess
import collections
from textwrap import dedent

import rnaseqde.utils as utils
from rnaseqde.task.base import CommandLineTask

from logging import getLogger


logger = getLogger(__name__)


class AlignTophat2Task(CommandLineTask):
    instances = []
    in_array = True
    script = utils.actpath_to_sympath(__file__)


    @property
    def inputs(self):
        inputs_ = {'--output-dir': self.output_dir}

        binding = {
                '--index': '--tophat2-index',
                '--gtf': '--gtf',
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

    def output(self, input: str):
        output_dir_ = super().output_dir
        sub_output_dir = utils.basename_replaced_ext('.fastq.gz', '', input)
        output_dir_ = os.path.join(self.output_dir, sub_output_dir)
        os.makedirs(output_dir_, exist_ok=True)

        return output_dir_

    @property
    def outputs(self):
        if self.inputs['--layout'] == 'sr':
            fastq1s = self.inputs['--fastq']
        else:
            fastq1s = self.inputs['--fastq'][0::2]

        samples = self.inputs['--sample'] if self.inputs['--sample'] else fastq1s

        outputs_ = super().inputs

        for k, v in [
            ('--bam', 'accepted_hits.bam'),
            ('--summary', 'align_summary.txt')
        ]:
            outputs_[k] = [os.path.join(self.output_subdir(s), v) for s in samples]

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
    Wrapper for UGE: Align reads to the reference genome using TopHat2

    Usage:
        align_tophat2 [options] --index <PATH> --gtf <PATH> [--sample <STR>...] --fastq <PATH>...

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

    task = AlignTophat2Task()
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
        '--GTF': '--gtf'
    }

    opt = utils.dictbind(opt_static, opt_runtime, binding)

    opt_ = {
        'fr': {'--library-type': 'fr-secondstrand'},
        'rf': {'--library-type': 'fr-firststrand'},
        'none': {'--library-type': 'fr-unstranded'}
    }
    opt.update(opt_[opt_runtime['--strandness']])

    args = [None] * 2
    args[0] = opt_runtime['--index']

    for f1, f2, s in zip(fastq1s, fastq2s, samples):
        if f2 == '':
            args[1] = f1
        else:
            args[1] = ' '.join([f1, f2])

        opt['-o'] = task.output_subdir(s)
        os.makedirs(task.output_subdir(s), exist_ok=True)

        cmd = "{base} {opt} {args}".format(
            base='tophat2',
            opt=utils.optdict_to_str(opt),
            args=' '.join(args)
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
