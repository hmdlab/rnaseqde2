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
from rnaseqde.task.base import CommandLineTask


class ConvStringtieToRawTask(CommandLineTask):
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

    @property
    def outputs(self):
        outputs_ = self._inputs
        outputs_.update({
            f"--{v}-mat-csv": os.path.join(self.output_dir, f"{v}_count_matrix.csv") for v in ['gene', 'transcript']
            })

        return outputs_

    def puts_list_targets(self, inputs, samples):
        targets = [os.path.abspath(input) for input in inputs]
        list_targets = os.path.join(self.output_dir, 'list_targets.txt')
        body = ['\t'.join([name, path]) for name, path in zip(samples, targets)]

        with open(list_targets, 'w+') as f:
            f.write('\n'.join(body))

        return list_targets


def main():
    """
    Wrapper for UGE: Generate count matrix using PrepDE.py

    Usage:
        conv_stringtie2raw [options] --sample <STR>... --quantified-gtf <PATH>...

    Options:
        --sample <STR>...           : Sample(s)
        --output-dir <PATH>         : Output directory [default: .]
        --dry-run                   : Dry-run [default: False]
        --quantified-gtf <PATH>...  : Quantified GTF file(s)

    """

    task = ConvStringtieToRawTask()
    opt_runtime = utils.docmopt(main.__doc__)

    task.output_dir = opt_runtime['--output-dir']

    if not opt_runtime['--dry-run']:
        os.makedirs(task.output_dir, exist_ok=True)
        list_targets = task.puts_list_targets(
            opt_runtime['--quantified-gtf'],
            opt_runtime['--sample']
            )

        opt = {
            '-i': list_targets,
            '-g': task.outputs['--gene-mat-csv'],
            '-t': task.outputs['--transcript-mat-csv']
        }

        cmd = "{base} {opt}".format(
            base='prepDE.py',
            opt=utils.optdict_to_str(opt)
            )

        sys.stderr.write("Command: {}\n".format(cmd))

        proc = subprocess.run(cmd, shell=True, capture_output=True)
        utils.puts_captured_output(proc, task.output_dir)


if __name__ == '__main__':
    main()
