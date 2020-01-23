#! /usr/bin/env python3

from copy import deepcopy

from rnaseqde.task.base import Task, DictWrapperTask
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


def init_dry_run_option(opt):
    Task.dry_run = opt['--dry-run']

    steps = {
        'align': [AlignStarTask, AlignHisat2Task, AlignTophat2Task, ConvSamToBamTask],
        'quant': [
            QuantKallistoTask, QuantStringtieTask, DeCuffdiffTask,
            ConvStringtieToRawTask, QuantRsemTask, ConvRsemToMatrixTask,
            ConvCuffdiffToRawTask, ConvAnyToRawTask
            ],
        'de': [DeEbseqTask, DeBallgownTask, DeSleuthTask, DeEdgerTask]
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
        AlignStarTask([beginning])
        AlignHisat2Task([beginning])
        AlignTophat2Task([beginning])
        QuantKallistoTask([beginning])

    for t in AlignHisat2Task.instances:
        ConvSamToBamTask([t])

    align_tasks = [AlignStarTask, ConvSamToBamTask, AlignTophat2Task]
    Task.dry_run = opt['--dry-run']

    # Queue quantification tasks
    for at in align_tasks:
        for t in at.instances:
            QuantStringtieTask([t])
            DeCuffdiffTask([t])

    for t in QuantStringtieTask.instances:
        ConvStringtieToRawTask([t])

    for t in AlignStarTask.instances:
        QuantRsemTask([t])

    for t in QuantRsemTask.instances:
        ConvRsemToMatrixTask([t])

    quant_tasks = [DeCuffdiffTask, QuantKallistoTask, QuantRsemTask, QuantStringtieTask]
    Task.dry_run = opt['--dry-run']

    for qt in quant_tasks:
        for t in qt.instances:
            if isinstance(t, DeCuffdiffTask):
                ConvCuffdiffToRawTask([t])
                continue
            ConvAnyToRawTask([t])

    # Queue DE tasks
    for t in ConvRsemToMatrixTask.instances:
        DeEbseqTask([t])

    for t in QuantStringtieTask.instances:
        DeBallgownTask([t])

    for t in QuantKallistoTask.instances:
        DeSleuthTask([t])

    for t in ConvAnyToRawTask.instances:
        for v in ['gene', 'transcript']:
            DeEdgerTask([t])

    # Check outputs of each task
    EndTask(
        required_tasks=Task.instances,
        excluded_tasks=DictWrapperTask.instances
    )

    Task.run_all_tasks()
