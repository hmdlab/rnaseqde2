#! /usr/bin/env python3
#$ -S $HOME/.pyenv/shims/python3
#$ -pe def_slot 8
#$ -l s_vmem=8G -l mem_req=8G
#$ -cwd
#$ -o ugelogs/
#$ -e ugelogs/

import sys
import os
import subprocess
from textwrap import dedent
import itertools
from collections import OrderedDict

import rnaseqde.utils as utils
from rnaseqde.task.base import CommandLineTask

from logging import getLogger


logger = getLogger(__name__)


class DeCuffdiffTask(CommandLineTask):
    instances = []
    in_array = False
    script = utils.actpath_to_sympath(__file__)

    @property
    def inputs(self):
        inputs_ = {'--output-dir': self.output_dir}

        binding = {
                '--gtf': '--gtf',
                '--strandness': '--strandness',
                '--group': '--group',
                '--dry-run': '--dry-run',
                '--bam': '--bam'
                }

        inputs_ = utils.dictbind(inputs_, super().inputs, binding)

        return inputs_

    @property
    def outputs(self):
        outputs_ = super().inputs

        for k, v in {
            '--transcript-tsv': 'isoform_exp.diff',
            '--transcript-raw-tsv': 'isoforms.read_group_tracking',
            '--gene-tsv': 'gene_exp.diff',
            '--gene-raw-tsv': 'genes.read_group_tracking'
        }.items():
            outputs_[k] = os.path.join(self.output_dir, v)

        return outputs_


def _grouped(groups, values):
    list_ = [(g, v) for g, v in zip(groups, values)]

    # CHANGE: Do NOT sort, keep order
    # list_.sort(key=lambda x: x[0])
    dict_ = OrderedDict()

    for key, group in itertools.groupby(list_, lambda x: x[0]):
        dict_[key] = [v for _, v in list(group)]

    return dict_


def main():
    """
    Wrapper for UGE: Perform DE analysis using Cuffdiff2

    Usage:
        de_cuffdiff [options] --gtf <PATH> --group <STR>... --bam <PATH>...

    Options:
        --gtf <PATH>         : GTF annotation file
        --strandness <TYPE>  : Library strandness (none/rf/fr) [default: none]
        --group <STR>...     : (Comma delimited) group(s)
        --output-dir <PATH>  : Output directory [default: .]
        --conf <PATH>        : Configuration file
        --dry-run            : Dry-run [default: False]
        --bam <PATH>...      : BAM file(s)

    """

    task = DeCuffdiffTask()

    opt_runtime = utils.docmopt(dedent(main.__doc__))
    opt_static = utils.load_conf(opt_runtime['--conf']) if opt_runtime['--conf'] else task.conf

    task.output_dir = opt_runtime['--output-dir']
    os.makedirs(task.output_dir, exist_ok=True)

    opt = opt_static

    opt_ = {
        'fr': {'--library-type': 'fr-secondstrand'},
        'rf': {'--library-type': 'fr-firststrand'},
        'none': {'--library-type': 'fr-unstranded'}
    }
    opt.update(opt_[opt_runtime['--strandness']])

    grouped_bam = _grouped(
        opt_runtime['--group'],
        opt_runtime['--bam']
        )

    opt['-L'] = ','.join(grouped_bam.keys())
    opt['-o'] = task.output_dir

    args = [None] * 2
    args[0] = opt_runtime['--gtf']
    args[1] = ' '.join([','.join(v) for v in grouped_bam.values()])

    cmd = "{base} {opt} {args}".format(
        base='cuffdiff',
        opt=utils.optdict_to_str(opt),
        args=' '.join(args)
    )

    sys.stderr.write("Command: {}\n".format(cmd))

    if not opt_runtime['--dry-run']:
        proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        with open(os.path.join(task.output_dir, 'stderr.log'), 'w') as f:
            f.write(proc.stderr.decode())

        with open(os.path.join(task.output_dir, 'stdout.log'), 'w') as f:
            f.write(proc.stdout.decode())


if __name__ == '__main__':
    main()
