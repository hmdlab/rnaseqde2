#! /usr/bin/env python3
#$ -S $HOME/.pyenv/shims/python3
#$ -l s_vmem=0.5G -l mem_req=0.5G
#$ -cwd
#$ -o ./ugelogs/
#$ -e ./ugelogs/

import sys
import os
import csv
from datetime import datetime

import rnaseqde.utils as utils
from rnaseqde.task.base import Task


class EndTask(Task):
    instances = []

    def run(self):
        self.submit_query(
            script=self.script,
            opt_script=' '.join(self.inputs),
            log=True
            )

    @property
    def inputs(self):
        outputs = [(t.job_id, output) for t in self.required_tasks if t.job_id is not None for output in t.outputs.values() if output and isinstance(output, str)]

        path = 'list_outputs.txt'
        with open(path, 'w') as f:
            for o in outputs:
                f.write("{}\n".format("\t".join(o)))

        return [path]

    @property
    def output_dir(self):
        return utils.from_root('')

    @property
    def outputs(self):
        return {__file__: self.script}


def main():
    input_ = sys.argv[1]

    # HACK: Use try except
    error_occurred = False
    messages = []

    cwd = utils.actpath_to_sympath(os.getcwd())

    with open(input_, 'r') as f:
        reader = csv.reader(f, delimiter="\t")

        for row in reader:
            _jid = row[0]
            _path = row[1]

            if cwd not in os.path.expandvars(_path):
                output_ = os.path.join(cwd, _path)
            else:
                output_ = _path

            if not utils.exists(output_):
                messages.append("[ERR] {}:{} doesn't exists.".format(_jid, _path))
                error_occurred = True

    if error_occurred:
        messages.append(datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
        with open('failed.txt', 'w') as f:
            f.write("\n".join(messages))
        sys.exit(1)

    messages.append('There are no errors.')
    messages.append(datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
    with open('successful.txt', 'w') as f:
        f.write("\n".join(messages))


if __name__ == '__main__':
    main()
