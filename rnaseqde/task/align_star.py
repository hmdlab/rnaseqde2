#! /usr/bin/env python3
#$ -S $HOME/.pyenv/shims/python3
#$ -pe def_slot 4
#$ -l s_vmem=16G -l mem_req=16G
#$ -cwd
#$ -o ugelogs/
#$ -e ugelogs/

import os
import subprocess
from textwrap import dedent

from docopt import docopt

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
        keys = ['--star-index', '--gtf', '--fastq', '--layout', '--strandness', '--dry-run', '--verbose']
        inputs_ = utils.dictfilter(super().inputs, keys)
        inputs_['--output-dir'] = self.output_dir

        binding = {
                '--index': '--star-index',
                '--gtf': '--gtf',
                '--output-dir': '--output-dir',
                '--layout': '--layout',
                '--strandness': '--strandness',
                '': '--fastq'
                }

        inputs_ = utils.dictbind({}, inputs_, binding)

        return inputs_

    def output_prefix(self, input, base_dir):
        prefix_ = os.path.join(
            base_dir,
            utils.basename_replaced_ext('.fastq.gz', '', input),
            '')

        return prefix_

    @property
    def outputs(self):
        if self.inputs['--layout'] == 'sr':
            fastq = self.inputs['<fastq>']
        else:
            fastq = self.inputs['<fastq>'][0::2]

        dict_ = super().inputs

        binding = {
            '--bam': 'Aligned.sortedByCoord.out.bam',
            '--transcript-bam': 'Aligned.toTranscriptome.out.bam',
            '--sjdb': 'SJ.out.tab'
        }

        for k, v in binding.items():
            dict_[k] = [os.path.join(self.output_prefix(f), v) for f in fastq]

        return dict_

    @property
    # TBD: Should implement on the super class or not
    def qsub_threads(self):
        d = 1 if self.inputs['--layout'] == 'sr' else 2
        n_tasks = len(next(reversed(self.inputs.values()))) / d
        return self._qsub_threads(n_tasks)


def main():
    """
    Wrapper for UGE: Align reads to the reference genome using STAR

    Usage:
        align_star [options] <fastq>...

    Options:
        --index <PATH>       : Reference index file
        --gtf <PATH>         : GTF annotation file
        --layout <TYPE>      : Library layout (sr/pe) [default: sr]
        --strandness <TYPE>  : Library strandness (none/rf/fr) [default: none]
        --output-dir <PATH>  : Output directory [default: .]
        --sample <STR>       : (Comma delimited) sample(s)
        --conf <PATH>        : Configure file
        --dry-run            : Dry-run [default: False]
        --verbose            : Verbose [default: False]
        <fastq>...           : (Ordered) FASTQ file(s)
    """

    task = AlignStarTask()
    opt_runtime = docopt(dedent(main.__doc__))
    opt_static = utils.load_conf(opt_runtime['--conf']) if opt_runtime['--conf'] else task.conf

    if opt_runtime['--layout'] == 'sr':
        fastq1 = utils.scattered(opt_runtime['<fastq>'])
        fastq2 = [''] * len(opt_runtime['<fastq>'])

    if opt_runtime['--layout'] == 'pe':
        fastq1 = utils.scattered(opt_runtime['<fastq>'][0::2])
        fastq2 = utils.scattered(opt_runtime['<fastq>'][1::2])

    samples = opt_runtime['--sample'].split(',') if opt_runtime['--sample'] else fastq1
    if len(samples) != len(fastq1):
        raise('Invalid sample argument specified.')

    binding = {
        '--genomeDir': '--index',
        '--sjdbGTFfile': '--gtf'
    }

    opt = utils.dictbind(opt_static, opt_runtime, binding)

    for i, (f1, f2, s) in enumerate(zip(fastq1, fastq2, samples)):
        opt['--readFilesIn'] = ' '.join((f1, f2)).strip()
        opt['--outFileNamePrefix'] = task.output_prefix(s, opt_runtime['--output-dir'])

        os.makedirs(opt['--outFileNamePrefix'], exist_ok=True)

        cmd = "{base} {opt}".format(
            base='STAR',
            opt=utils.optdict_to_str(opt)
        )
        logger.debug(cmd)

        if not opt_runtime['--dry-run']:
            subprocess.run(cmd, shell=True)


if __name__ == '__main__':
    main()
