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


class AlignStarTask(CommandLineTask):
    instances = []
    in_array = True
    script = utils.actpath_to_sympath(__file__)

    @property
    def inputs(self):
        inputs_ = {'--output-dir': self.output_dir}

        binding = {
                '--index': '--star-index',
                '--gtf': '--gtf',
                '--layout': '--layout',
                '--strandness': '--strandness',
                '--sample': '--sample',
                '--dry-run': '--dry-run',
                '--fastq': '--fastq'
                }

        inputs_ = utils.dictbind(inputs_, super().inputs, binding)

        return inputs_

    def output_prefix(self, input):
        prefix_ = os.path.join(
            self.output_dir,
            utils.basename_replaced_ext('.fastq.gz', '', input),
            ''
            )

        os.makedirs(prefix_, exist_ok=True)

        return prefix_

    @property
    def outputs(self):
        if self.inputs['--layout'] == 'sr':
            fastq1s = self.inputs['--fastq']
        else:
            fastq1s = self.inputs['--fastq'][0::2]

        samples = self.inputs['--sample'] if self.inputs['--sample'] else fastq1s

        dict_ = super().inputs

        binding = {
            '--bam': 'Aligned.sortedByCoord.out.bam',
            '--transcript-bam': 'Aligned.toTranscriptome.out.bam',
            '--sjdb': 'SJ.out.tab'
        }

        for k, v in binding.items():
            dict_[k] = [os.path.join(self.output_prefix(s), v) for s in samples]

        return dict_

    @property
    # TBD: Should implement on the super class or not
    def qsub_threads(self):
        d = 1 if self.inputs['--layout'] == 'sr' else 2
        n_tasks = len(self.inputs['--fastq']) / d
        return self._qsub_threads(n_tasks)


def main():
    """
    Wrapper for UGE: Align reads to the reference genome using STAR

    Usage:
        align_star [options] --index <PATH> --gtf <PATH> --fastq <PATH>... [--sample <STR>...]

    Options:
        --index <PATH>       : Reference index file
        --gtf <PATH>         : GTF annotation file
        --fastq <PATH>...    : (Ordered) FASTQ file(s)
        --layout <TYPE>      : Library layout (sr/pe) [default: sr]
        --strandness <TYPE>  : Library strandness (none/rf/fr) [default: none]
        --output-dir <PATH>  : Output directory [default: .]
        --sample <STR>...    : (Comma delimited) sample(s)
        --conf <PATH>        : Configuration file
        --dry-run            : Dry-run [default: False]

    """

    task = AlignStarTask()

    opt_runtime = utils.docmopt(dedent(main.__doc__))
    opt_static = utils.load_conf(opt_runtime['--conf']) if opt_runtime['--conf'] else task.conf

    task.output_dir = opt_runtime['--output-dir']

    if opt_runtime['--layout'] == 'sr':
        fastq1s = utils.scattered(opt_runtime['--fastq'])
        fastq2s = [''] * len(opt_runtime['--fastq'])

    if opt_runtime['--layout'] == 'pe':
        fastq1s = utils.scattered(opt_runtime['--fastq'][0::2])
        fastq2s = utils.scattered(opt_runtime['--fastq'][1::2])

    if opt_runtime['--sample']:
        samples = utils.scattered(opt_runtime['--sample'])
    else:
        samples = fastq1s

    if len(samples) != len(fastq1s):
        raise Exception(
            "Invalid sample argument specified {} vs {}".format(len(samples), len(fastq1s))
        )

    binding = {
        '--genomeDir': '--index',
        '--sjdbGTFfile': '--gtf'
    }

    opt = utils.dictbind(opt_static, opt_runtime, binding)

    for f1, f2, s in zip(fastq1s, fastq2s, samples):
        opt['--readFilesIn'] = ' '.join((f1, f2)).strip()
        opt['--outFileNamePrefix'] = task.output_prefix(s)

        cmd = "{base} {opt}".format(
            base='STAR',
            opt=utils.optdict_to_str(opt)
        )

        sys.stderr.write("Command: {}\n".format(cmd))

        if not opt_runtime['--dry-run']:
            proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            with open(os.path.join(task.output_prefix(s), 'stderr.log'), 'w') as f:
                f.write(proc.stderr.decode())

            with open(os.path.join(task.output_prefix(s), 'stdout.log'), 'w') as f:
                f.write(proc.stdout.decode())


if __name__ == '__main__':
    main()
