"""
rnaseqde.utils
~~~~~~~~~~~~~~

This module provides utility functions.
"""

import sys
import os
import re
import glob
from pathlib import Path
from copy import deepcopy
import itertools
from typing import List
from collections import OrderedDict
from docopt import docopt

import yaml

from logging import getLogger


logger = getLogger(__name__)


def root_path():
    abspath_actual = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return actpath_to_sympath(abspath_actual)


def from_root(relpath):
    # NOTE: Change from module root to app root
    return os.path.join(root_path(), relpath)


def actpath_to_sympath(abspath_actual):
    # NOTE: For handling path from singularity container
    home_path_actual = str(Path.home().resolve())
    home_path_symbolic = str(Path.home())

    sympath_ = re.sub(
        "^{}".format(home_path_actual),
        home_path_symbolic, abspath_actual, 1
        )

    return sympath_


def load_conf(relpath, strict=True):
    try:
        with open(from_root(relpath)) as f:
            dict_ = yaml.load(f)
    except FileNotFoundError as e:
        if strict:
            logger.exception(e)
            sys.exit()

        dict_ = {}
    return dict_


def docmopt(doc, **kwargs):
    def tidyargv(argv: list, prefix='--'):
        list_ = []
        for v in argv:
            if v.startswith(prefix):
                p = v
                continue

            list_.append(p)
            list_.append(v)
        return list_

    kwargs.update({
            'argv': tidyargv(sys.argv[1:]),
            'options_first': True
        })

    return docopt(doc, **kwargs)


def dictbind(src: dict, dist: dict, binding: dict):
    dict_ = OrderedDict(deepcopy(src))
    for k, v in binding.items():
        dict_[k] = dist[v]

    return(dict_)


def dictfilter(src: dict, keys: list):
    dict_ = {}
    for k in keys:
        dict_[k] = src[k]

    return(dict_)


def optdict_to_str(dict_, delimiter=' ', tidy=False):
    list_ = []

    for k, v in dict_.items():
        if v is None:
            continue

        if type(v) is list:
            if tidy:
                for v_ in v:
                    list_.append(k)
                    list_.append(v_)
                continue
            else:
                list_.append(k)
                list_.append(delimiter.join(v))
                continue

        if type(v) is bool:
            if v:
                list_.append(k)
                continue
            else:
                continue

        list_.append(k)
        list_.append(str(v))
        continue

    str_ = delimiter.join(list_)
    return str_


def stripped(key):
    return key.lstrip('--').lstrip('<').rstrip('>')


def uri2path(uri):
    return uri.lstrip('file://')


def gathered(list_dict: List[dict], key):
    list_ = []
    for ld in list_dict:
        list_.append(ld[key])
    return list_


def basename_replaced_ext(ext_target, ext_replacement, input):
    basename = os.path.basename(input)
    pattern = re.compile(r"{}$".format(ext_target))
    basename_replaced = re.sub(pattern, '', basename)
    basename_replaced += ext_replacement

    return basename_replaced


def pack_vars(locals_: locals, *vars):
    if not vars:
        return {k: v for k, v in locals_.items() if not k.startswith('__') and k not in ['self', 'cls', 'k', 'v']}

    ids = [id(var) for var in vars]
    return {k: v for k, v in locals_.items() if id(v) in ids}


def camel_cased(str_: str):
    return re.sub(r"_(.)", lambda x: x.group(1).upper(), str_)


def snake_cased(str_: str):
    str_ = str_[0].lower() + str_[1:]
    return re.sub(r"([A-Z])", lambda x: '_' + x.group(1).lower(), str_)


def dict_globed(dir):
    files = [os.path.splitext(path) for path in sorted(
        glob.glob("{}/**".format(dir), recursive=True)) if not os.path.isdir(path)]
    files.sort(key=lambda x: x[1])

    dict_ = {}
    for k, g in itertools.groupby(files, lambda x: x[1]):
        dict_[k] = [root + ext for root, ext in g]

    return dict_


def nested_list_to_variables(nested_list_):
    for i, l in enumerate(nested_list_):
        locals()['v' + str(i)] = l

    exec("return " + ", ".join(["v{}".format(_) for _ in range(-~i)]))


def flatten(nested_list):
    list_ = []
    for item in nested_list:
        if isinstance(item, list):
            list_.extend(flatten(item))
        else:
            list_.append(item)

    return list_


def clean():
    pass
