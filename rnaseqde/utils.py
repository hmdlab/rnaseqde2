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
from textwrap import dedent
import itertools
from typing import Union, List

from docopt import docopt, parse_defaults
import yaml


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
            dict_ = yaml.safe_load(f)
    except FileNotFoundError as e:
        if strict:
            sys.stderr.write("{}".format(str(e)))
            sys.exit()

        dict_ = {}
    return dict_


def docmopt(doc, **kwargs):
    # HACK: DO NOT have state
    def tidyargv(argv: list, prefixes=['--', '-']):
        list_ = []
        is_open = False
        for v in argv:
            if any(map(v.startswith, prefixes)):
                # NOTE: Lazy eval
                if is_open:
                    list_.append(p)

                p = v
                is_open = True
                continue

            list_.append(p)
            list_.append(v)
            is_open = False

        if is_open:
            list_.append(p)

        return list_

    doc = dedent(doc)

    try:
        argv = kwargs.pop('argv')
    except KeyError:
        argv = sys.argv[1:]

    kwargs.update(
        {
            'argv': tidyargv(argv),
            'help': True,
            'options_first': True
        })

    return docopt(doc, **kwargs)


def docopt_keys(doc):
    doc = dedent(doc)
    opts = parse_defaults(doc)
    keys = [o.name for o in opts]

    return keys


def dictbind(dist: dict, src: dict, binding: dict):
    dist_ = deepcopy(dist)
    for k, v in binding.items():
        dist_[k] = src[v]

    return(dist_)


def dictfilter(src: dict, include=None, exclude=None):
    if include:
        dist_ = {}
        for k in include:
            try:
                dist_[k] = src[k]
            except KeyError:
                pass

    if exclude:
        try:
            dist_
        except NameError:
            dist_ = deepcopy(src)

        for k in exclude:
            try:
                del dist_[k]
            except NameError:
                pass

    return(dist_)


def dictupdate_if_exists(dist: Union[list, dict], src: dict):
    if type(dist) is list:
        dist = {k: None for k in dist}

    if type(dist) is dict:
        dist_ = deepcopy(dist)
        dist_.update(dictfilter(src, include=dist.keys()))
        return dist_

    raise TypeError(f"dist must type of list or dict: {type(dist)}")


def flatten(nested_list):
    list_ = []
    for item in nested_list:
        if isinstance(item, list):
            list_.extend(flatten(item))
        else:
            list_.append(item)

    return list_


def dictcombine(src: List[dict], default=None, exclude=None):
    # NOTE: Lost order info
    keys = set(flatten([list(s.keys()) for s in src]))

    dict_ = {}
    for k in keys:
        dict_[k] = [s.get(k, default) for s in src if s.get(k, default) != exclude]

    return dict_


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


# NOTE: Change bypass flag
def puts_captured_output(proc, output_dir='.', bypass=False):
    with open(os.path.join(output_dir, 'stderr.log'), 'w') as f:
        f.write(proc.stderr.decode())

    with open(os.path.join(output_dir, 'stdout.log'), 'w') as f:
        f.write(proc.stdout.decode())

    if bypass:
        sys.stdout.write(proc.stdout.decode())
        sys.stdout.write(proc.stderr.decode())


def replaced_ext(ext_target, ext_replacement, input):
    pattern = re.compile(r"{}$".format(ext_target))
    replaced = re.sub(pattern, '', input)
    replaced += ext_replacement

    return replaced


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


def exists(path, strict=False):
    path = os.path.expandvars(path)

    if os.path.exists(path):
        return True

    if not strict:
        if glob.glob(f"{path}*"):
            return True

    return False


# XXX:
def nested_list_to_variables(nested_list_):
    for i, l in enumerate(nested_list_):
        locals()['v' + str(i)] = l

    exec("return " + ", ".join(["v{}".format(_) for _ in range(-~i)]))


def clean():
    pass
