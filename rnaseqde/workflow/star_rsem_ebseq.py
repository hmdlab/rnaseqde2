#! /usr/bin/env python3

from copy import deepcopy

from rnaseqde.task.base import Task, DictWrapperTask
from rnaseqde.task.end import EndTask

from rnaseqde.task.align_star import AlignStarTask
from rnaseqde.task.quant_rsem import QuantRsemTask
from rnaseqde.task.conv_rsem2mat import ConvRsemToMatrixTask
from rnaseqde.task.de_ebseq import DeEbseqTask


def run(opt, assets):
    Task.dry_run = opt['--dry-run']

    annotations = assets[opt['--reference']]
    if opt['--annotation']:
        annotations = {k: v for k, v in annotations.items() if k == opt['--annotation']}

    # Queue alignment tasks
    for k, v in annotations.items():
        opt_ = deepcopy(opt)
        opt_.update(v)
        AlignStarTask([
            DictWrapperTask(opt_, output_dir=k)
            ])

    # Queue quantification tasks
    for t in AlignStarTask.instances:
        QuantRsemTask([t])

    for t in QuantRsemTask.instances:
        ConvRsemToMatrixTask([t])

    # Queue DE tasks
    for t in ConvRsemToMatrixTask.instances:
        DeEbseqTask([t])

    EndTask(
        required_tasks=Task.instances,
        excluded_tasks=DictWrapperTask.instances
    )

    Task.run_all_tasks()
