#! /usr/bin/env python3
#$ -S $HOME/.pyenv/shims/python3
#$ -pe def_slot 4
#$ -l s_vmem=4G -l mem_req=4G
#$ -cwd
#$ -o ugelogs/
#$ -e ugelogs/

import sys
import os
import subprocess

import rnaseqde.utils as utils
from rnaseqde.task.base import ArrayTask


class AlignTophat2Task(ArrayTask):
    instances = []

    @property
    def inputs(self):
        inputs_ = utils.dictupdate_if_exists(
            utils.docopt_keys(main.__doc__),
            self._inputs
        )

        inputs_.update({
            '--index': self._inputs['--tophat2-index'],
            '--output-dir': self.output_dir
            })

        return inputs_

    def suboutput_dir(self, input):
        suboutput_dir_ = os.path.join(
            self.output_dir,
            utils.basename_replaced_ext('.fastq.gz', '', input)
            )

        return suboutput_dir_

    def suboutputs(self, input):
        binding = {
            '--bam': 'accepted_hits.bam',
            '--summary': 'align_summary.txt'
        }

        return self._suboutputs(input, binding)

    @property
    def outputs(self):
        def _samples():
            if self.inputs['--sample'] is not None:
                return self.inputs['--sample']
            else:
                if self.inputs['--layout'] == 'sr':
                    return self.incrementer
                else:
                    return self.incrementer[0:2]

        samples = _samples()

        outputs_ = self._inputs
        outputs_.update(
            utils.dictcombine([self.suboutputs(s) for s in samples])
        )

        return outputs_

    @property
    def n_tasks(self):
        if self.inputs['--layout'] == 'pe':
            return int(self._n_tasks() / 2)

        return self._n_tasks()


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

    opt_runtime = utils.docmopt(main.__doc__)
    task = AlignTophat2Task(
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
        '--GTF': '--gtf'
    }

    opt = utils.dictbind(task.conf, opt_runtime, binding)

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

        opt['-o'] = task.suboutput_dir(s)

        cmd = "{base} {opt} {args}".format(
            base='tophat2',
            opt=utils.optdict_to_str(opt),
            args=' '.join(args)
            )

        sys.stderr.write("Command: {}\n".format(cmd))

        if not opt_runtime['--dry-run']:
            os.makedirs(task.suboutput_dir(s), exist_ok=True)
            proc = subprocess.run(cmd, shell=True, capture_output=True)
            utils.puts_captured_output(proc, task.suboutput_dir(s))


if __name__ == '__main__':
    main()
