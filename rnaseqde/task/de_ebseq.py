#! /usr/bin/env python3
#$ -S $HOME/.pyenv/shims/python3
#$ -l s_vmem=8G -l mem_req=8G
#$ -cwd
#$ -o ugelogs/
#$ -e ugelogs/

import os
from argparse import ArgumentParser
import subprocess
import collections

import rnaseqde.utils as utils
from rnaseqde.decorator import carefully_run
from rnaseqde.task.base import (
    Task,
    CommandLineTask,
)


class DeEbseqTask(CommandLineTask):
    """
    Command:
        Rscript scripts/rsem-for-ebseq-find-DE.R <path_to_ebseq_lib> [ngvec] <gene-transcript-matrix> <output_prefix> [<conditions>...]

    Example:
        Rscript scripts/rsem-for-ebseq-find-DE.R . transcripts.ngvec GeneMat.txt GeneMat.results 3 3
    """
    instances = []

    # base_command = "rsem-run-ebseq"
    base_command = "Rscript {}".format(utils.from_root('scripts/rsem-for-ebseq-find-DE.R'))
    iter_keys = None
    script = utils.resolve_to_symbolic(__file__)
    in_parallel = False

    def argparser(self):
        parent_parser = Task.argparser()

        parser = ArgumentParser(
            description='DE analysis using EBSeq',
            parents=[parent_parser])
        parser.add_argument(
            '--gene-mat-tsv', type=str, required=False,
            help='Count matrix (gene)')
        parser.add_argument(
            '--transcript-mat-tsv', type=str, required=False,
            help='Count matrix (transcript)')
        parser.add_argument(
            '--conditions', nargs='*', type=str, required=True,
            help='Conditions')
        parser.add_argument(
            '--ngvector', type=str, required=True,
            help='Ng vector for transcript-level analysis')

        return parser

    @property
    def inputs(self):
        inputs_ = super().inputs

        inputs_['ngvector'] = inputs_.pop('ebseq-ngvector')

        group = inputs_.pop('group')

        # FIXME: Optimistic coding
        inputs_['conditions'] = ' '.join([str(v) for v in collections.Counter(group).values()])

        return inputs_

    @property
    def outputs(self):
        for v in ['gene', 'transcript']:
            locals()[v + '-tsv'] = os.path.join(self.output_dir, v, 'results.tsv')

        return utils.pack_vars(locals())


def main():
    task = DeEbseqTask()
    subprocess.run = carefully_run(subprocess.run)

    os.makedirs(task.output_dir, exist_ok=True)

    for unit in ['gene', 'transcript']:
        output_dir_ = os.path.join(task.output_dir, unit)
        key_ = "{}-mat-tsv".format(unit)
        os.makedirs(output_dir_, exist_ok=True)

        # HACK: To simple
        try:
            positional_args
        except NameError:
            positional_args = [None] * 5

        if unit == 'gene':
            ngvector = "'#'"

        if unit == 'transcript':
            ngvector = task.args.pop('ngvector') or ''

        # This script only can specify postional args[0..4]
        positional_args[0] = '.'
        positional_args[1] = ngvector
        positional_args[2] = task.args.pop(key_)
        positional_args[3] = os.path.join(output_dir_, 'results.tsv')
        positional_args[4] = ' '.join(task.args['conditions'])

        if None in positional_args:
            for i, _ in enumerate(positional_args):
                if _ is None:
                    raise Exception("Positional arg{} is not assigned.".format(i))

        command = "{} {}".format(
            task.base_command, ' '.join(positional_args))

        print(command)

        if not task.dry_run:
            subprocess.run(command)


if __name__ == '__main__':
    main()
