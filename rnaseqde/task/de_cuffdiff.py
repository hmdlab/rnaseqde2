#! /usr/bin/env python3
#$ -S $HOME/.pyenv/shims/python3
#$ -pe def_slot 6
#$ -l s_vmem=24G -l mem_req=24G
#$ -l d_rt=192:00:00 -l s_rt=192:00:00
#$ -cwd
#$ -o ugelogs/
#$ -e ugelogs/

import sys
import os
import subprocess
import itertools

import rnaseqde.utils as utils
from rnaseqde.task.base import CommandLineTask


class DeCuffdiffTask(CommandLineTask):
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
        binding = {
            '--transcript-tsv': 'isoform_exp.diff',
            '--transcript-raw-tsv': 'isoforms.read_group_tracking',
            '--gene-tsv': 'gene_exp.diff',
            '--gene-raw-tsv': 'genes.read_group_tracking'
        }

        outputs_.update({
            k: os.path.join(self.output_dir, v)for k, v in binding.items()
            })

        return outputs_


def _grouped(groups, values):
    list_ = [(g, v) for g, v in zip(groups, values)]

    # CHANGE: Do NOT sort, keep order
    # list_.sort(key=lambda x: x[0])
    dict_ = {}

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

    opt_runtime = utils.docmopt(main.__doc__)
    task = DeCuffdiffTask(
        output_dir=opt_runtime['--output-dir'],
        conf=opt_runtime['--conf']
        )

    opt = task.conf

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
    os.makedirs(task.output_dir, exist_ok=True)

    if not opt_runtime['--dry-run']:
        proc = subprocess.run(cmd, shell=True, capture_output=True)
        utils.puts_captured_output(proc, task.output_dir)


if __name__ == '__main__':
    main()
