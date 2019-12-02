#! /usr/bin/env python3

"""
RNA-Seq DE analysis pipeline using Universal Grid Engine on NIG super computer

Usage:
    rnaseqde [options] <sample_sheet>

Options:
    --layout <TYPE>      : Library layout (sr/pe) [default: sr]
    --strandness <TYPE>  : Library strandness (none/rf/fr) [default: none]
    --reference NAME              : Reference name [default: grch38]
    --annotation NAME             : Annotation name (in the case using only one annotation)
    --dry-run                     : Dry-run [default: False]
    --verbose                     : Verbose [default: False]
    <sample_sheet>                : Tab-delimited text that contained the following columns:
                                    sample; fastq1[fastq2]; group

Supported references:
    grch38

Supported annotations:
    all (default)
    gencode
    gencode_basic
    gencode_refeseq
    refeseq
"""

import sys
import logging
from copy import deepcopy

from schema import Schema, Or, SchemaError
from docopt import docopt

import rnaseqde.utils as utils
from rnaseqde.sample_sheet_manager import SampleSheetManager
from rnaseqde.task.base import Task, DictWrapperTask
from rnaseqde.task.align_star import AlignStarTask

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
        '--layout': Or('sr', 'pe'),
        '--strandness': Or('none', 'rf', 'fr'),
        '--reference': Or(None, str),
        '--annotation': Or(None, str),
        '--dry-run': bool,
        '--verbose': bool,
        '<sample_sheet>': str
    })

    try:
        opt = schema.validate(opt)
        return opt
    except SchemaError as e:
        logger.exception(e)
        sys.exit(1)


def main():
    opt = _opt_validated(docopt(__doc__))
    opt.update(SampleSheetManager(opt['<sample_sheet>']).to_dict())

    Task.dry_run = opt['--dry-run']

    assets = utils.load_conf('config/assets.yml')
    annotations = assets[opt['--reference']]
    if opt['--annotation']:
        annotations = {k: v for k, v in annotations.items() if k == opt['--annotation']}

    for k, v in annotations.items():
        opt_ = deepcopy(opt)
        opt_.update(v)
        beginning = DictWrapperTask(opt_, k)
        AlignStarTask([beginning])

    Task.run_all_tasks()


if __name__ == '__main__':
    main()