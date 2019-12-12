#! /usr/bin/env python3

from copy import deepcopy

from rnaseqde.task.base import Task, DictWrapperTask
from rnaseqde.task.end import EndTask

from rnaseqde.task.align_star import AlignStarTask
from rnaseqde.task.quant_rsem import QuantRsemTask
from rnaseqde.task.conv_rsem2ebseq_mat import ConvRsemToEbseqMatrixTask
from rnaseqde.task.de_ebseq import DeEbseqTask

from rnaseqde.task.align_hisat2 import AlignHisat2Task
from rnaseqde.task.conv_sam2bam import ConvSamToBamTask
from rnaseqde.task.quant_stringtie import QuantStringtieTask
from rnaseqde.task.prep_prepde import PrepPrepdeTask
from rnaseqde.task.de_ballgown import DeBallgownTask

from rnaseqde.task.align_tophat2 import AlignTophat2Task
from rnaseqde.task.de_cuffdiff import DeCuffdiffTask

from rnaseqde.task.quant_kallisto import QuantKallistoTask
from rnaseqde.task.de_sleuth import DeSleuthTask

from rnaseqde.task.conv_any2raw_tximport import ConvAny2RawTximportTask
from rnaseqde.task.de_edger import DeEdgerTask


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
        AlignStarTask([beginning])
        AlignHisat2Task([beginning])
        AlignTophat2Task([beginning])
        QuantKallistoTask([beginning])

    for t in AlignHisat2Task.instances:
        ConvSamToBamTask([t])

    align_tasks = [AlignStarTask, ConvSamToBamTask, AlignTophat2Task]

    # Queue quantification tasks
    for at in align_tasks:
        for t in at.instances:
            QuantStringtieTask([t])
            DeCuffdiffTask([t])

    for t in QuantStringtieTask.instances:
        PrepPrepdeTask([t])

    for t in AlignStarTask.instances:
        QuantRsemTask([t])

    for t in QuantRsemTask.instances:
        ConvRsemToEbseqMatrixTask([t])

    quant_tasks = [DeCuffdiffTask, QuantKallistoTask, QuantRsemTask, QuantStringtieTask]

    for qt in quant_tasks:
        for t in qt.instances:
            ConvAny2RawTximportTask([t])

    # Queue DE tasks
    for t in ConvRsemToEbseqMatrixTask.instances:
        DeEbseqTask([t])

    for t in QuantStringtieTask.instances:
        DeBallgownTask([t])

    for t in QuantKallistoTask.instances:
        DeSleuthTask([t])

    for t in ConvAny2RawTximportTask.instances:
        DeEdgerTask([t])

    EndTask(
        required_tasks=Task.instances,
        excepted_tasks=[beginning]
    )

    Task.run_all_tasks()
