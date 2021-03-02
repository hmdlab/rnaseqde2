#! /usr/bin/env python3
#$ -S $HOME/.pyenv/shims/python3
#$ -l s_vmem=16G -l mem_req=16G
#$ -cwd
#$ -o ugelogs/
#$ -e ugelogs/

import sys
import os
import subprocess
import collections

import rnaseqde.utils as utils
from rnaseqde.task.base import CommandLineTask


class DeEbseqTask(CommandLineTask):
    instances = []

    @property
    def inputs(self):
        inputs_ = utils.dictupdate_if_exists(
            utils.docopt_keys(main.__doc__),
            self._inputs
        )

        inputs_.update({
            '--ngvector': self._inputs['--ebseq-ngvector'],
            '--output-dir': self.output_dir
            })

        return inputs_

    @property
    def outputs(self):
        outputs_ = self._inputs
        binding = {
            "--ebseq-{}-result-tsv": 'result.tsv',
            "--ebseq-{}-result-norm-tsv": 'result.tsv.normalized_data_matrix'
            }

        for v in ['gene', 'transcript']:
            for key, val in binding.items():
                outputs_[key.format(v)] = os.path.join(self.output_dir, v, val)

        return outputs_


def main():
    """
    Wrapper for UGE: Perform DE analysis using EBSeq

    Usage:
        de_ebseq [options] --ngvector <PATH> --group <STR>... --gene-mat-tsv <PATH> --transcript-mat-tsv <PATH>

    Options:
        --ngvector <PATH>            : NgVector file
        --group <STR>...             : (Comma delimited) group(s)
        --output-dir <PATH>          : Output directory [default: .]
        --dry-run                    : Dry-run [default: False]
        --gene-mat-tsv <PATH>        : Gene-level count matrix file
        --transcript-mat-tsv <PATH>  : Transcrit-level count matrix file

    """

    task = DeEbseqTask()
    opt_runtime = utils.docmopt(main.__doc__)

    task.output_dir = opt_runtime['--output-dir']

    # NOTE: Input matrix MUST ordered by group
    n_reps = [str(v) for v in collections.Counter(opt_runtime['--group']).values()]

    for v in ['gene', 'transcript']:
        key_ = "--{}-mat-tsv".format(v)
        if opt_runtime[key_] is None:
            continue

        output_dir_ = os.path.join(task.output_dir, v)

        opt = {
            '--ngvector': "'#'" if v == 'gene' else opt_runtime['--ngvector'],
            '--level': v,
            '--output-dir': output_dir_
        }

        args = [None] * 3
        args[0] = opt_runtime[key_]
        args[1], args[2] = n_reps

        cmd = "{base} {script} {opt} {args}".format(
            base='Rscript',
            script=utils.from_root('scripts/de_ebseq.R'),
            opt=utils.optdict_to_str(opt),
            args=' '.join(args)
            )

        sys.stderr.write("Command: {}\n".format(cmd))

        if not opt_runtime['--dry-run']:
            os.makedirs(output_dir_, exist_ok=True)
            proc = subprocess.run(cmd, shell=True, capture_output=True)
            utils.puts_captured_output(proc, output_dir_)


if __name__ == '__main__':
    main()
