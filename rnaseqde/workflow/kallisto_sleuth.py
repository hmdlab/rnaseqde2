#! /usr/bin/env python3

from copy import deepcopy

from rnaseqde.task.base import Task, DictWrapperTask
from rnaseqde.task.end import EndTask

from rnaseqde.task.quant_kallisto import QuantKallistoTask
from rnaseqde.task.de_sleuth import DeSleuthTask


def init_dry_run_option(opt):
    Task.dry_run = opt['--dry-run']

    steps = {
        'align': [],
        'quant': [QuantKallistoTask],
        'de': [DeSleuthTask]
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

    # Queue quantification tasks
    if opt['--resume-from'] in ['de']:
        Task.dry_run = True

    for k, v in annotations.items():
        opt_ = deepcopy(opt)
        opt_.update(v)
        beginning = DictWrapperTask(opt_, output_dir=k)
        QuantKallistoTask([beginning])

    Task.dry_run = opt['--dry-run']

    # Queue DE tasks
    for t in QuantKallistoTask.instances:
        DeSleuthTask([t])

    EndTask(
        required_tasks=Task.instances,
        excluded_tasks=DictWrapperTask.instances
    )

    Task.run_all_tasks()
