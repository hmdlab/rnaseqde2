#! /usr/bin/env python3

from copy import deepcopy

from rnaseqde.task.base import Task, DictWrapperTask
from rnaseqde.task.end import EndTask

from rnaseqde.task.quant_kallisto import QuantKallistoTask
from rnaseqde.task.de_sleuth import DeSleuthTask


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
        QuantKallistoTask([beginning])

    for t in QuantKallistoTask.instances:
        DeSleuthTask([t])

    EndTask(
        required_tasks=Task.instances,
        excepted_tasks=[beginning]
    )

    Task.run_all_tasks()
