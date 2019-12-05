#! /usr/bin/env python3

"""
RNA-Seq DE analysis pipeline using Universal Grid Engine on NIG super computer

Usage:
    rnaseqde [options] <sample_sheet>

Options:
    --layout <TYPE>      : Library layout (sr/pe) [default: sr]
    --strandness <TYPE>  : Library strandness (none/rf/fr) [default: none]
    --reference <NAME>   : Reference name [default: grch38]
    --annotation <NAME>  : Annotation name (in the case using only one annotation)
    --dry-run            : Dry-run [default: False]
    <sample_sheet>       : Tab-delimited text that contained the following columns:
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
from rnaseqde.task.end import EndTask

from rnaseqde.task.align_star import AlignStarTask
from rnaseqde.task.quant_rsem import QuantRsemTask
from rnaseqde.task.conv_rsem2ebseq_mat import ConvRsemToEbseqMatrixTask
from rnaseqde.task.de_ebseq import DeEbseqTask

from rnaseqde.task.align_hisat2 import AlignHisat2Task
from rnaseqde.task.conv_sam2bam import ConvSamToBamTask
from rnaseqde.task.quant_stringtie import QuantStringtieTask
from rnaseqde.task.prep_prepde import PrepPrepdeTask
from rnaseqde.task.de_ballgown import DeBallgownTask

from rnaseqde.task.align_tophat2 import AlignTophat2Task
from rnaseqde.task.de_cuffdiff import DeCuffdiffTask

# from rnaseqde.task.quant_kallisto import QuantKallistoTask
# from rnaseqde.task.de_sleuth import DeSleuthTask


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
    opt.update(
        SampleSheetManager(
            opt['<sample_sheet>'],
            (opt['--layout'] == 'pe')).to_dict()
        )

    Task.dry_run = opt['--dry-run']

    assets = utils.load_conf('config/assets.yml')
    annotations = assets[opt['--reference']]
    if opt['--annotation']:
        annotations = {k: v for k, v in annotations.items() if k == opt['--annotation']}

    # Queue alignment tasks
    for k, v in annotations.items():
        opt_ = deepcopy(opt)
        opt_.update(v)
        beginning = DictWrapperTask(opt_, output_dir=k)
        AlignStarTask([beginning])
        AlignHisat2Task([beginning])
        AlignTophat2Task([beginning])
        # QuantKallistoTask([beginning])

    ConvSamToBamTask(AlignHisat2Task.instances)

    align_tasks = [AlignStarTask, ConvSamToBamTask, AlignTophat2Task]

    # Queue quantification tasks
    for at in align_tasks:
        for t in at.instances:
            QuantStringtieTask([t])
            DeCuffdiffTask([t])

    for t in QuantStringtieTask.instances:
        PrepPrepdeTask([t])

    for t in AlignStarTask.instances:
        QuantRsemTask([t])

    for t in QuantRsemTask.instances:
        ConvRsemToEbseqMatrixTask([t])

    quant_tasks = [ConvRsemToEbseqMatrixTask, QuantStringtieTask]

    # Queue DE tasks
    for qt in quant_tasks:
        for t in qt.instances:
            pass

    for t in ConvRsemToEbseqMatrixTask.instances:
        DeEbseqTask([t])

    for t in QuantStringtieTask.instances:
        DeBallgownTask([t])

    # for t in QuantKallistoTask.instances:
    #     DeSleuthTask([t])

    # EndTask(
    #     required_tasks=Task.instances,
    #     excepted_tasks=[beginning]
    #     )

    Task.run_all_tasks()


if __name__ == '__main__':
    main()
