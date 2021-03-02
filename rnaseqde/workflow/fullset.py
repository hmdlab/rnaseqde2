#! /usr/bin/env python3

from copy import deepcopy
from functools import partial

from rnaseqde.task.base import Task, CommandLineTask, DictWrapperTask
from rnaseqde.task.end import EndTask

from rnaseqde.task.align_star import AlignStarTask
from rnaseqde.task.quant_rsem import QuantRsemTask
from rnaseqde.task.conv_rsem2mat import ConvRsemToMatrixTask
from rnaseqde.task.de_ebseq import DeEbseqTask

from rnaseqde.task.align_hisat2 import AlignHisat2Task
from rnaseqde.task.conv_sam2bam import ConvSamToBamTask
from rnaseqde.task.quant_stringtie import QuantStringtieTask
from rnaseqde.task.conv_stringtie2raw import ConvStringtieToRawTask
from rnaseqde.task.de_ballgown import DeBallgownTask

from rnaseqde.task.align_tophat2 import AlignTophat2Task
from rnaseqde.task.de_cuffdiff import DeCuffdiffTask

from rnaseqde.task.quant_kallisto import QuantKallistoTask
from rnaseqde.task.de_sleuth import DeSleuthTask

from rnaseqde.task.conv_any2raw import ConvAnyToRawTask
from rnaseqde.task.conv_cuffdiff2raw import ConvCuffdiffToRawTask
from rnaseqde.task.de_edger import DeEdgerTask


def init_options(opt):
    Task.dry_run = opt['--dry-run']

    steps = {
        'align': [AlignStarTask, AlignHisat2Task, AlignTophat2Task, ConvSamToBamTask],
        'quant': [QuantKallistoTask, QuantStringtieTask, QuantRsemTask],
        'de': [
            ConvRsemToMatrixTask, ConvCuffdiffToRawTask, ConvAnyToRawTask,
            DeCuffdiffTask, DeEbseqTask, DeBallgownTask, DeSleuthTask, DeEdgerTask]
    }

    if opt['--step-by-step'] is not None:
        Task.dry_run = True

        for t in steps[opt['--step-by-step']]:
            t.dry_run = False

        return

    if opt['--resume-from'] is not None:
        if opt['--resume-from'] in ['quant', 'de']:
            for t in steps['align']:
                t.dry_run = True

        if opt['--resume-from'] in ['de']:
            for t in steps['quant']:
                t.dry_run = Truee

        return


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
        beginning = DictWrapperTask(opt_)
        AlignStarTask([beginning], conf=conf)
        AlignHisat2Task([beginning], conf=conf)
        AlignTophat2Task([beginning], conf=conf)
        QuantKallistoTask([beginning], conf=conf)

    for t in AlignHisat2Task.instances:
        ConvSamToBamTask([t], conf=conf)

    align_tasks = [AlignStarTask, ConvSamToBamTask, AlignTophat2Task]

    # Queue quantification tasks
    for at in align_tasks:
        for t in at.instances:
            QuantStringtieTask([t], conf=conf)
            DeCuffdiffTask([t], conf=conf)

    for t in QuantStringtieTask.instances:
        ConvStringtieToRawTask([t], conf=conf)

    for t in AlignStarTask.instances:
        QuantRsemTask([t], conf=conf)

    for t in QuantRsemTask.instances:
        ConvRsemToMatrixTask([t], conf=conf)

    quant_tasks = [DeCuffdiffTask, QuantKallistoTask,
                   QuantRsemTask, QuantStringtieTask]

    for qt in quant_tasks:
        for t in qt.instances:
            if isinstance(t, DeCuffdiffTask):
                ConvCuffdiffToRawTask([t], conf=conf)
                continue
            ConvAnyToRawTask([t])

    # Queue DE tasks
    for t in ConvRsemToMatrixTask.instances:
        DeEbseqTask([t], conf=conf)

    for t in QuantStringtieTask.instances:
        DeBallgownTask([t], conf=conf)

    for t in QuantKallistoTask.instances:
        DeSleuthTask([t], conf=conf)

    for t in ConvAnyToRawTask.instances:
        for v in ['gene', 'transcript']:
            DeEdgerTask([t], conf=conf, level=v)

    # Check outputs of each task
    Task.run_all_tasks()
    EndTask(Task.instances).run()
