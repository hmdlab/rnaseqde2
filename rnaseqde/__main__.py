#! /usr/bin/env python3

"""
RNA-Seq DE analysis pipeline using Universal Grid Engine on NIG super computer

Usage:
    rnaseqde [options] <sample_sheet>

Options:
    --workflow <TYPE>    : Workflow [default: fullset]
    --layout <TYPE>      : Library layout (sr/pe) [default: sr]
    --strandness <TYPE>  : Library strandness (none/rf/fr) [default: none]
    --reference <NAME>   : Reference name [default: grch38]
    --annotation <NAME>  : Annotation name (in the case using only one annotation)
    --dry-run            : Dry-run [default: False]
    <sample_sheet>       : Tab-delimited text that contained the following columns:
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
    refeseq

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
    schema = Schema({
        '--workflow': Or(
            'fullset',
            'tophat2-cuffdiff',
            'star-rsem-ebseq',
            'hisat2-stringtie-ballgown',
            'kallisto-sleuth'
            ),
        '--layout': Or('sr', 'pe'),
        '--strandness': Or('none', 'rf', 'fr'),
        '--reference': Or(None, 'grch38'),
        '--annotation': Or(
            None,
            'gencode',
            'gencode_basic',
            'gencode_refeseq',
            'refeseq'
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
    opt.update(
        SampleSheetManager(
            opt['<sample_sheet>'],
            (opt['--layout'] == 'pe')).to_dict()
    )

    assets = utils.load_conf('config/assets.yml')

    workflows = {
        'fullset': fullset,
        'tophat2-cuffdiff': tophat2_cuffdiff,
        'star-rsem-ebseq': star_rsem_ebseq,
        'hisat2-stringtie-ballgown': hisat2_stringtie_ballgown,
        'kallisto-sleuth': kallisto_sleuth
    }

    wf = workflows[opt['--workflow']]
    wf.run(opt, assets)
    sys.exit(0)


if __name__ == '__main__':
    main()
