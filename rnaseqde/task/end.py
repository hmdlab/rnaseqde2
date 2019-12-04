#! /usr/bin/env python3
#$ -S $HOME/.pyenv/shims/python3
#$ -cwd
#$ -o ./ugelogs/
#$ -e ./ugelogs/

import sys
import os
from datetime import datetime

import rnaseqde.utils as utils
from rnaseqde.task.base import Task


class EndTask(Task):
    instances = []
    in_array = False
    script = utils.actpath_to_sympath(__file__)

    def __init__(
            self,
            required_tasks=None,
            excepted_tasks=None,
            **kwargs):
        super().__init__(required_tasks=required_tasks, **kwargs)
        self.excepted_tasks = excepted_tasks

    def run(self):
        self.submit_query(
            script=self.__class__.script,
            opt_script=' '.join(self.inputs)
            )

    @property
    def inputs(self):
        inputs_ = [output for task in self.required_tasks for output in task.outputs.values() if output]
        inputs_excepted = [output for task in self.excepted_tasks for output in task.outputs.values() if output]
        inputs_ = set(utils.flatten(inputs_)) - set(utils.flatten(inputs_excepted))

        return inputs_

    @property
    def output_dir(self):
        pass

    @property
    def outputs(self):
        return {__file__: self.__class__.script}


def main():
    task_outputs = sys.argv[1:]
    error_occured = False
    messages = []

    cwd = os.getcwd()
    utils.actpath_to_sympath(cwd)
    print(cwd)

    for output in task_outputs:
        if cwd in output:
            if not os.path.exists(output):
                messages.append("[ERR] {} doesn't exists.".format(output))
                error_occured = True
        else:
            messages.append("[WRN] {} passed.".format(output))

    if error_occured:
        with open('failed.txt', 'w') as f:
            sys.stderr.write("\n".join(messages))
            f.write("\n".join(messages))
    else:
        messages.append('Processes are completed.')
        messages.append(datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
        with open('completed.txt', 'w') as f:
            f.write("\n".join(messages))


if __name__ == '__main__':
    main()
