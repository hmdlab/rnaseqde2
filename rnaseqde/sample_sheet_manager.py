"""
rnaseqde.option_manager
~~~~~~~~~~~~~~~~~~~~~~~

This module manage command line options.
"""

import sys
import os
import csv
import logging
from collections import defaultdict

import inflection


logger = logging.getLogger('__main__')


class SampleSheetManager:
    def __init__(self, sample_sheet, is_paired=False):
        self._is_paired = is_paired
        self._dict = defaultdict(list)
        with open(sample_sheet) as f:
            csv_reader = csv.DictReader(f, delimiter='\t')
            fields = csv_reader.fieldnames
            for row in csv_reader:
                for field in fields:
                    self._dict[field].append(row[field])
        self._validate()

    def _validate(self):
        fields = self._dict.keys()
        fields_required = ['sample', 'group', 'fastq1']
        if self._is_paired:
            fields_required.append('fastq2')
        for field in fields_required:
            if field not in fields:
                sys.stderr.write("field: {} is required.".format(field))
                raise Exception
                sys.exit(1)

        samples = self.samples
        if len(samples) != len(set(samples)):
            sys.stderr.write('samples are not unique.')
            raise Exception
            sys.exit(1)

        read_files = self._ordered_fastqs()
        for file in read_files:
            if not os.path.exists(file):
                raise Exception("read file: {} does not exists.".format(file))
                sys.exit(1)

    @property
    def samples(self):
        return self._dict['sample']

    @property
    def groups(self):
        return self._dict['group']

    def _ordered_fastqs(self, tupled=False):
        fastq1s = self._dict['fastq1']
        if not self._is_paired:
            return fastq1s

        fastq2s = self._dict['fastq2']
        fastqs_paired = [(read1, read2) for read1, read2 in zip(fastq1s, fastq2s)]
        if tupled:
            return fastqs_paired

        return [fastq for fastq_paired in fastqs_paired for fastq in fastq_paired]

    @property
    def fastq1s(self):
        return self._dict['fastq1']

    @property
    def fastq2s(self):
        return self._dict['fastq2']

    @property
    def fastqs(self):
        return self._ordered_fastqs()

    @property
    def fastq_paired(self):
        return self.ordered_read_file(tupled=True)

    def to_dict(self):
        attributes = ['sample', 'group', 'fastq', 'fastq1', 'fastq2']

        return {'--' + attr: getattr(self, inflection.pluralize(attr)) for attr in attributes}
