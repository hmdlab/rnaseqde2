#! /usr/bin/env python3
#$ -S $HOME/.pyenv/shims/python3
#$ -l s_vmem=0.5G -l mem_req=0.5G
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

    def __init__(
            self,
            required_tasks=None,
            excluded_tasks=None,
            **kwargs):
        super().__init__(required_tasks=required_tasks, **kwargs)
        self.excluded_tasks = excluded_tasks

    def run(self):
        self.submit_query(
            script=self.script,
            opt_script=' '.join(self.inputs),
            log=False
            )

    @property
    def inputs(self):
        inputs_ = [output for task in self.required_tasks for output in task.outputs.values() if output]
        inputs_excluded = [output for task in self.excluded_tasks for output in task.outputs.values() if output]

        inputs_ = set(utils.flatten(inputs_)) - set(utils.flatten(inputs_excluded))

        return inputs_

    @property
    def output_dir(self):
        return utils.from_root('')

    @property
    def outputs(self):
        return {__file__: self.script}


def main():
    task_outputs = sys.argv[1:]

    # HUCK: Use try except
    error_occured = False
    messages = []

    cwd = utils.actpath_to_sympath(os.getcwd())

    for output in task_outputs:
        if cwd not in output:
            output_ = os.path.join(cwd, output)
        else:
            output_ = output

        if not os.path.exists(output_):
            messages.append("[ERR] {} doesn't exists.".format(output))
            error_occured = True

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
