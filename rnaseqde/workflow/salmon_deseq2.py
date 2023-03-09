#! /usr/bin/env python3

from copy import deepcopy

from rnaseqde.task.base import Task, DictWrapperTask
from rnaseqde.task.end import EndTask

from rnaseqde.task.conv_any2raw import ConvAnyToRawTask
from rnaseqde.task.quant_salmon import QuantSalmonTask
from rnaseqde.task.de_deseq2 import DeDeseq2Task


def init_options(opt):
    Task.dry_run = opt['--dry-run']
    Task.ar_id = opt['--ar']

    steps = {
        'align': [],
        'quant': [QuantSalmonTask],
        'de': [DeDeseq2Task]
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
        QuantSalmonTask([beginning], conf=conf)

    for t in QuantSalmonTask.instances:
        ConvAnyToRawTask([t], conf=conf)

    # Queue DE tasks
    for t in ConvAnyToRawTask.instances:
        for v in ['gene', 'transcript']:
            DeDeseq2Task([t], conf=conf, level=v)

    Task.run_all_tasks()
    EndTask(Task.instances).run()
