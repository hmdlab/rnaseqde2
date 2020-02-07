#! /usr/bin/env python3

from copy import deepcopy

from rnaseqde.task.base import Task, DictWrapperTask
from rnaseqde.task.end import EndTask

from rnaseqde.task.align_hisat2 import AlignHisat2Task
from rnaseqde.task.conv_sam2bam import ConvSamToBamTask
from rnaseqde.task.quant_stringtie import QuantStringtieTask
from rnaseqde.task.de_ballgown import DeBallgownTask


def init_dry_run_option(opt):
    Task.dry_run = opt['--dry-run']

    steps = {
        'align': [AlignHisat2Task, ConvSamToBamTask],
        'quant': [QuantStringtieTask],
        'de': [DeBallgownTask]
    }

    if opt['--resume-from'] in ['quant', 'de']:
        for t in steps['align']:
            t.dry_run = True

    if opt['--resume-from'] in ['de']:
        for t in steps['quant']:
            t.dry_run = True


def run(opt, assets):
    init_dry_run_option(opt)

    annotations = assets[opt['--reference']]
    if opt['--annotation']:
        annotations = {k: v for k, v in annotations.items() if k == opt['--annotation']}

    # Queue alignment tasks
    if opt['--resume-from'] in ['quant', 'de']:
        Task.dry_run = True

    for k, v in annotations.items():
        opt_ = deepcopy(opt)
        opt_.update(v)
        beginning = DictWrapperTask(opt_, output_dir=k)
        AlignHisat2Task([beginning])

    for t in AlignHisat2Task.instances:
        ConvSamToBamTask([t])

    align_tasks = [ConvSamToBamTask]

    # Queue quantification tasks
    if opt['--resume-from'] in ['de']:
        Task.dry_run = True

    for at in align_tasks:
        for t in at.instances:
            QuantStringtieTask([t])


    # Queue DE tasks
    for t in QuantStringtieTask.instances:
        DeBallgownTask([t])

    EndTask(
        required_tasks=Task.instances,
        excluded_tasks=DictWrapperTask.instances
    )

    Task.run_all_tasks()
