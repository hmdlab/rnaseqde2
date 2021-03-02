#! /usr/bin/env python3

"""
RNA-Seq DE analysis pipeline using Universal Grid Engine on NIG supercomputer

Usage:
    rnaseqde [options] <sample_sheet>

Options:
    --workflow <TYPE>     : Workflow [default: fullset]
    --conf <PATH>         : Directory contain configure files for each tool
    --layout <TYPE>       : Library layout (sr/pe) [default: sr]
    --strandness <TYPE>   : Library strandness (none/rf/fr) [default: none]
    --reference <NAME>    : Reference name [default: grch38]
    --annotation <NAME>   : Annotation name (in the case using only one annotation)
    --step-by-step <TYPE> : Run with step (align/quant/de)
    --assets <PATH>       : Assets yml path
    --resume-from <TYPE>  : Resume workflow from (align/quant/de)
    --dry-run             : Dry-run [default: False]
    <sample_sheet>        : Tab-delimited text that contained the following columns:
                            sample; fastq1[fastq2]; group

Workflows:
    fullset (default)
    tophat2-cuffdiff
    star-rsem-ebseq
    hisat2-stringtie-ballgown
    kallisto-sleuth

Supported references:
    grch38 (default)

Supported annotations:
    all (default)
    gencode
    gencode_basic
    gencode_refeseq

"""

import sys

from schema import Schema, Or, SchemaError
from docopt import docopt

from rnaseqde.sample_sheet_manager import SampleSheetManager
from rnaseqde.workflow import (
    fullset,
    tophat2_cuffdiff,
    star_rsem_ebseq,
    hisat2_stringtie_ballgown,
    kallisto_sleuth
)
import rnaseqde.utils as utils

import logging
from logging import (
    getLogger,
    StreamHandler,
    Formatter
)


logger = getLogger('rnaseqde')
logger.setLevel(logging.DEBUG)
handler = StreamHandler()
handler.setFormatter(Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)


def _opt_validated(opt):
    # TODO: Generate Schema object from config files
    schema = Schema({
        '--annotation': Or(None, str),
        '--reference': Or(None, str),
        '--assets': Or(None, str),
        '--workflow': Or(
            'fullset',
            'tophat2-cuffdiff',
            'star-rsem-ebseq',
            'hisat2-stringtie-ballgown',
            'kallisto-sleuth',
            'check-outputs'
            ),
        '--conf': Or(None, str),
        '--layout': Or('sr', 'pe'),
        '--strandness': Or('none', 'rf', 'fr'),
        '--step-by-step': Or(
            None,
            'align',
            'quant',
            'de'
            ),
        '--resume-from': Or(
            None,
            'align',
            'quant',
            'de'
            ),
        '--dry-run': bool,
        '<sample_sheet>': str
    })

    try:
        opt = schema.validate(opt)
        return opt
    except SchemaError as e:
        sys.stderr.write("Invalid options were specified:\n")
        sys.stderr.write(str(e))
        sys.exit(1)


def main():
    opt = _opt_validated(docopt(__doc__))

    if sum([True for k in ['--step-by-step', '--resume-from', '--dry-run'] if opt[k]]) > 1:
        sys.stderr.write("--dry-run, --step-by-step and --resume-from cannot be specified at the same time.")
        sys.exit(1)

    opt.update(
        SampleSheetManager(
            opt['<sample_sheet>'],
            (opt['--layout'] == 'pe')).to_dict()
    )

    if opt['--assets'] is None:
        assets = utils.load_conf(utils.from_root('config/assets.yml'))
    else:
        assets = utils.load_conf(opt['--assets'])

    def _exists_reference(key, assets):
        keys_defined = [k for k in assets.keys()]
        return key in keys_defined

    def _exists_annotation(key, assets):
        keys_defined = [k2 for v1 in assets.values() if type(v1) == dict for k2 in v1.keys()]
        return key in keys_defined

    # HACK: Move to _opt_validated
    if opt['--reference']:
        if not _exists_reference(opt['--reference'], assets):
            sys.stderr.write("Invalid options were specified:\n")
            sys.stderr.write("reference: {}".format(opt['--reference']))
            sys.exit(1)

    if opt['--annotation']:
        if not _exists_annotation(opt['--annotation'], assets):
            sys.stderr.write("Invalid options were specified:\n")
            sys.stderr.write("annotation: {}".format(opt['--annotation']))
            sys.exit(1)

    workflows = {
        'fullset': fullset,
        'tophat2-cuffdiff': tophat2_cuffdiff,
        'star-rsem-ebseq': star_rsem_ebseq,
        'star-rsem-ebseq-gencode_refseq_noncode': star_rsem_ebseq,
        'hisat2-stringtie-ballgown': hisat2_stringtie_ballgown,
        'kallisto-sleuth': kallisto_sleuth,
        'fullset-ercc': fullset
    }

    wf = workflows[opt['--workflow']]
    wf.run(opt, assets)


if __name__ == '__main__':
    main()
