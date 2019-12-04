"""
rnaseqde.task.base
~~~~~~~~~~~~~~~~~~~~~~~

This module define base task class
"""

import sys
import os
import re
import random
import subprocess
from abc import ABCMeta, abstractmethod

import rnaseqde.utils as utils

from logging import getLogger


logger = getLogger(__name__)


class Task(metaclass=ABCMeta):
    instances = []
    dry_run = False
    in_array = None
    scripts = None

    def __init__(
            self,
            required_tasks=None,
            **kwargs):

        self.required_tasks = required_tasks
        self.kwargs = kwargs
        self._job_id = None
        self._output_dir = None
        self.register()

    @classmethod
    def run_all_tasks(cls):
        for task in cls.instances:
            task.run()

    @classmethod
    def task_job_ids(cls):
        return [task.job_id for task in cls.tasks]

    def submit_query(self, script, opt_script):
        def _build_command():
            if not os.environ.get('SGE_TASK_ID', None):
                cmd = "{script} {opt_script}".format(
                    script=script,
                    opt_script=opt_script
                    )
                return cmd

            opt = {
                '-V': True,
                '-terse': True,
                '-N': self.task_name,
                '-hold_jid': self._qsub_hold_job_ids
            }

            if self.__class__.in_array:
                opt.update(
                    {'-t': self._qsub_threads}
                )

            cmd = "{base} {opt} {script} {opt_script}".format(
                base='qsub',
                opt=utils.optdict_to_str(opt),
                script=script,
                opt_script=opt_script
                )
            return cmd

        cmd = _build_command()
        logger.debug("Task name: {}".format(self.task_name))
        logger.debug("Command: {}".format(cmd))

        if not self.__class__.dry_run:
            proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if not self.__class__.dry_run and os.environ.get('SGE_TASK_ID', None):
            self.job_id = proc.stdout
        else:
            self._job_id = str(random.randrange(1000))

        logger.info("Job_ID: {} was submitted.".format(self.job_id))

    def register(self):
        self.__class__.instances.append(self)
        if not self.__class__.__name__ == 'Task':
            Task.instances.append(self)

    def upper(self):
        return self.required_tasks[0]

    @property
    def job_id(self):
        return self._job_id

    @job_id.setter
    def job_id(self, stdout: bytes):
        self._job_id = stdout.decode().strip().split('.')[0]

    @property
    def task_name(self):
        return re.sub(r"_task$", '', utils.snake_cased(self.__class__.__name__))

    @property
    def _qsub_threads(self):
        # NOTE: Obtain last value from ordered dict
        n_tasks = len(next(reversed(self.inputs.values())))
        step = 1
        return "1-{}:{}".format(str(int(n_tasks)), step)

    @property
    def _qsub_hold_job_ids(self):
        if self.required_tasks is not None:
            try:
                job_ids = ','.join(
                    set([task.job_id for task in set(self.required_tasks) if task.job_id is not None])
                )

                if job_ids == '':
                    return None

                return job_ids
            except TypeError:
                return None

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def inputs(self):
        pass

    @abstractmethod
    def output_dir(self):
        pass

    @abstractmethod
    def outputs(self):
        pass


class CommandLineTask(Task):
    def __init__(
            self,
            required_tasks=None,
            **kwargs):

        super().__init__(required_tasks=required_tasks)
        self.conf = utils.load_conf("config/task/{}.yml".format(self.task_name), strict=False)

    def run(self):
        os.makedirs(self.output_dir, exist_ok=True)

        self.submit_query(
            script=self.__class__.script,
            opt_script=utils.optdict_to_str(self.inputs)
            )

    @property
    def inputs(self):
        inputs_ = {}

        if self.required_tasks is not None:
            for task in reversed(self.required_tasks):
                if task.outputs is not None:
                    inputs_.update(task.outputs)

        return inputs_

    @property
    def output_dir(self):
        if self._output_dir is not None:
            return self._output_dir

        if self.required_tasks is not None:
            return os.path.join(self.upper().output_dir, self.task_name)
        else:
            return self.task_name

    @output_dir.setter
    def output_dir(self, output_dir):
        self._output_dir = output_dir

    @classmethod
    def scattered(cls, inputs):
        try:
            sge_task_id = os.environ.get('SGE_TASK_ID', None)
            sge_task_id = int(sge_task_id)
        except ValueError:
            pass
        except TypeError:
            logger.info("Run on local.\n")
            return inputs
        else:
            return [inputs[~-sge_task_id]]


class DictWrapperTask(Task):
    def __init__(self, opt: dict, output_dir=''):
        self._opt = opt
        self._output_dir = output_dir
        self._job_id = None

    def run(self):
        pass

    @property
    def inputs(self):
        pass

    @property
    def output_dir(self):
        return self._output_dir

    @property
    def outputs(self):
        return self._opt
