import errno
import os
import sys
from functools import wraps

is_py2 = sys.version_info[0] == 2

if is_py2:
    StringTypes = (str, unicode)
else:
    StringTypes = (str,)

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


def mock_func(func):
    @wraps(func)
    def mock(self, *args, **kwargs):
        func(self, *args, **kwargs)

    return mock


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
