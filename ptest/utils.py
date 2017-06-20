import ctypes
import errno
import os
import sys
import time
import traceback
import types

if sys.version_info[0] == 2:
    StringTypes = (str, unicode)
else:
    StringTypes = (str,)

if sys.version_info[0] == 2:
    from urlparse import urljoin
    from urllib import unquote, pathname2url
else:
    from urllib.parse import urljoin, unquote
    from urllib.request import pathname2url

def make_dirs(dir_path):
    try:
        os.makedirs(dir_path)
    except OSError as e:
        if e.errno != errno.EEXIST:  # be happy if someone already created the path
            raise


def remove_tree(dir_path, remove_root=True):
    if os.path.exists(dir_path):
        for root, dirs, files in os.walk(dir_path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        if remove_root is True:
            os.rmdir(dir_path)


def is_coroutine_function(func):
    if sys.version_info[:2] >= (3, 4):
        import asyncio
        return asyncio.iscoroutinefunction(func)
    return False


def mock_func(func):
    fn = types.FunctionType(func.__code__, func.__globals__, func.__name__, func.__defaults__, func.__closure__)
    # in case fun was given attrs (note this dict is a shallow copy):
    fn.__dict__.update(func.__dict__)
    return fn


def call_function(func, *args, **kwargs):
    if is_coroutine_function(func):
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(func.__call__(*args, **kwargs))
    return func.__call__(*args, **kwargs)


def kill_thread(thread):
    """
        Kill a python thread from another thread.

    :param thread: a threading.Thread instance
    """
    exc = ctypes.py_object(SystemExit)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
        ctypes.c_long(thread.ident), exc)
    if res == 0:
        raise ValueError("nonexistent thread id")
    elif res > 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")

    start_time = time.time()
    while (time.time() - start_time) <= 30:
        if not thread.isAlive():
            return
        time.sleep(1)

    raise SystemError("Timed out waiting for thread <%s> to be killed." % thread)


def format_thread_stack(thread):
    stack_code = ["Stack Trace:"]
    stack = sys._current_frames()[thread.ident]
    for file_name, line_no, name, line in traceback.extract_stack(stack):
        stack_code.append("  File: \"%s\", line %d, in %s" % (file_name, line_no, name))
        if line:
            stack_code.append("    %s" % (line.strip()))
    return "\n".join(stack_code)


def escape_html(obj):
    if isinstance(obj, dict):
        return {key: escape_html(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [escape_html(item) for item in obj]
    if isinstance(obj, StringTypes):
        return obj.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") \
            .replace(" ", "&nbsp;").replace('"', "&quot;").replace("\n", "<br/>")
    return obj


def escape_filename(name):
    _name = name
    escape_list = [
        ("%", "%25"),
        ("\\", "%5C"),
        ("/", "%2F"),
        (":", "%3A"),
        ("*", "%01"),
        ("?", "%3F"),
        ("\"", "%22"),
        ("<", "%3C"),
        (">", "%3E"),
        ("|", "%7C")
    ]
    for char, to in escape_list:
        _name = _name.replace(char, to)
    return _name
