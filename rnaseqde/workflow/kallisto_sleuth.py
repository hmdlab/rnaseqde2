#! /usr/bin/env python3

from copy import deepcopy

from rnaseqde.task.base import Task, DictWrapperTask
from rnaseqde.task.end import EndTask

from rnaseqde.task.quant_kallisto import QuantKallistoTask
from rnaseqde.task.de_sleuth import DeSleuthTask


def init_options(opt):
    Task.dry_run = opt['--dry-run']
    Task.ar_id = opt['--ar']

    steps = {
        'align': [],
        'quant': [QuantKallistoTask],
        'de': [DeSleuthTask]
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

    # Queue quantification tasks
    for k, v in annotations.items():
        opt_ = deepcopy(opt)
        opt_.update(v)
        beginning = DictWrapperTask(opt_, output_dir=k)
        QuantKallistoTask([beginning], conf=conf)

    # Queue DE tasks
    for t in QuantKallistoTask.instances:
        DeSleuthTask([t], conf=conf)

    Task.run_all_tasks()
    EndTask(Task.instances).run()
