import calendar
import datetime
import os
import shutil
import sys
import traceback

from collections import ChainMap
from datetime import date
from datetime import datetime
from datetime import timedelta

from .constants import EXCEPTION_DATETIME_FMT

def insert_before_extension(base, insert_string):
    root, ext = os.path.splitext(base)
    filename = ''.join([root, insert_string, ext])
    return filename

def move_for_exception(source, move_to, exc):
    """
    Move `source` to destination `move_to` with the current datetime put in the
    filename. Write another file next to it in the destination, with the
    exception `exc` in it.
    """
    # capture now for both files
    now = datetime.now()
    now_string = now.strftime(EXCEPTION_DATETIME_FMT)

    source_base = os.path.basename(source)
    dest_fn = insert_before_extension(source_base, now_string)

    # combine with exception directory
    dest_path = os.path.join(move_to, dest_fn)

    # should be safe with a filename with a full datetime in it.
    shutil.move(source, dest_path)

    # write stacktrace
    stacktrace_fn = insert_before_extension(
        source_base,
        f'{now_string}.STACKTRACE.txt'
    )
    stacktrace_path = os.path.join(move_to, stacktrace_fn)
    with open(stacktrace_path, 'w') as stacktrace_fp:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        stack_string = ''.join(lines)
        stacktrace_fp.write(stack_string)
        stacktrace_fp.write(str(exc))

def keyed_sections(cp, prefix, sep='_', func=None):
    """
    Loop configparser sections starting with `prefix + sep`, creating a dict
    keyed on text after `sep` with values of dicts of that section. If a
    section named `prefix` exists it will be used as a base dict for the more
    specific keyed sections.

    (ignore spaces between in section names)
    [prefix]
    c = 5

    [prefix sep key1]
    a = 1

    [prefix sep key2]
    b = 2

    ...

    {'key1': {'a': '1', 'c': '5'}, 'key2': {'b': '2', 'c': '5'}, ...}

    :param cp: a ConfigParser instance
    :param prefix: first part of section name
    :param sep: separator string between first and last part
    :param func: a callable called on the dict values, useful for coercing types
    """
    if prefix in cp:
        base = cp[prefix]
    else:
        base = {}

    if func is None:
        func = lambda x: x

    def keyvalue(secname):
        key = secname[len(prefix):].partition(sep)[2]
        value = func(dict(ChainMap(cp[secname], base)))
        return (key, value)

    result = dict(
        keyvalue(secname) for secname in cp
        if secname.startswith(prefix + sep)
    )
    return result

def path_format_data(path):
    fmtdata = dict(
        path = path,
        now = datetime.now(),
    )
    head, tail = os.path.split(path)
    fmtdata['path_head'] = head # directory
    fmtdata['path_tail'] = tail # filename
    root, ext = os.path.splitext(tail)
    fmtdata['fn_root'] = root # filename without extension
    fmtdata['fn_ext'] = ext # extension with dot
    return fmtdata

def datetimerange(start, end, step=timedelta(days=1)):
    """
    Caller is responsible for correct start and end data types with respect to the step.
    """
    while start < end:
        yield start
        start += step

def startofmonth(value):
    return date(value.year, value.month, 1)

def endofmonth(value):
    return date(value.year, value.month, calendar.mdays[value.month])

def literal_sql(query, dialect):
    return query.compile(
        dialect = dialect,
        compile_kwargs = {"literal_binds": True}
    )

