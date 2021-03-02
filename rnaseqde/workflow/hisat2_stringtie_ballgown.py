#! /usr/bin/env python3

from copy import deepcopy

from rnaseqde.task.base import Task, DictWrapperTask
from rnaseqde.task.end import EndTask

from rnaseqde.task.align_hisat2 import AlignHisat2Task
from rnaseqde.task.conv_sam2bam import ConvSamToBamTask
from rnaseqde.task.quant_stringtie import QuantStringtieTask
from rnaseqde.task.de_ballgown import DeBallgownTask


def init_options(opt):
    Task.dry_run = opt['--dry-run']

    steps = {
        'align': [AlignHisat2Task, ConvSamToBamTask],
        'quant': [QuantStringtieTask],
        'de': [DeBallgownTask]
    }

    if opt['--step-by-step'] is not None:
        Task.dry_run = True

        for t in steps[opt['--step-by-step']]:
            t.dry_run = False

    if opt['--resume-from'] in ['quant', 'de']:
        for t in steps['align']:
            t.dry_run = True

    if opt['--resume-from'] in ['de']:
        for t in steps['quant']:
            t.dry_run = True


def run(opt, assets):
    init_options(opt)

    conf = opt.pop('--conf')

    annotations = assets[opt['--reference']]
    if opt['--annotation']:
        annotations = {k: v for k, v in annotations.items() if k == opt['--annotation']}

    # Queue alignment tasks
    for k, v in annotations.items():
        opt_ = deepcopy(opt)
        opt_.update(v)
        beginning = DictWrapperTask(opt_, output_dir=k)
        AlignHisat2Task([beginning], conf=conf)

    for t in AlignHisat2Task.instances:
        ConvSamToBamTask([t], conf=conf)

    align_tasks = [ConvSamToBamTask]

    # Queue quantification tasks
    for at in align_tasks:
        for t in at.instances:
            QuantStringtieTask([t], conf=conf)


    # Queue DE tasks
    for t in QuantStringtieTask.instances:
        DeBallgownTask([t], conf=conf)

    Task.run_all_tasks()
    EndTask(Task.instances).run()
