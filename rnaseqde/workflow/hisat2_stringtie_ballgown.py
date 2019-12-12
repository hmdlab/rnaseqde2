#! /usr/bin/env python3

from copy import deepcopy

from rnaseqde.task.base import Task, DictWrapperTask
from rnaseqde.task.end import EndTask

from rnaseqde.task.align_hisat2 import AlignHisat2Task
from rnaseqde.task.conv_sam2bam import ConvSamToBamTask
from rnaseqde.task.quant_stringtie import QuantStringtieTask
from rnaseqde.task.de_ballgown import DeBallgownTask


def run(opt, assets):
    Task.dry_run = opt['--dry-run']

    annotations = assets[opt['--reference']]
    if opt['--annotation']:
        annotations = {k: v for k, v in annotations.items() if k == opt['--annotation']}

    # Queue alignment tasks
    for k, v in annotations.items():
        opt_ = deepcopy(opt)
        opt_.update(v)
        beginning = DictWrapperTask(opt_, output_dir=k)
        AlignHisat2Task([beginning])

    for t in AlignHisat2Task.instances:
        ConvSamToBamTask([t])

    align_tasks = [ConvSamToBamTask]

    # Queue quantification tasks
    for at in align_tasks:
        for t in at.instances:
            QuantStringtieTask([t])

    # Queue DE tasks
    for t in QuantStringtieTask.instances:
        DeBallgownTask([t])

    EndTask(
        required_tasks=Task.instances,
        excepted_tasks=[beginning]
    )

    Task.run_all_tasks()
