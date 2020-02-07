#! /usr/bin/env python3

from copy import deepcopy

from rnaseqde.task.base import Task, DictWrapperTask
from rnaseqde.task.end import EndTask

from rnaseqde.task.align_tophat2 import AlignTophat2Task
from rnaseqde.task.de_cuffdiff import DeCuffdiffTask


def init_dry_run_option(opt):
    Task.dry_run = opt['--dry-run']

    steps = {
        'align': [AlignTophat2Task],
        'quant': [],
        'de': [DeCuffdiffTask]
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
    for k, v in annotations.items():
        opt_ = deepcopy(opt)
        opt_.update(v)
        beginning = DictWrapperTask(opt_, output_dir=k)
        AlignTophat2Task([beginning])

    align_tasks = [AlignTophat2Task]

    # Queue quantification and DE tasks
    for at in align_tasks:
        for t in at.instances:
            DeCuffdiffTask([t])

    EndTask(
        required_tasks=Task.instances,
        excluded_tasks=DictWrapperTask.instances
    )

    Task.run_all_tasks()
