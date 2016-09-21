import errno
import os
from functools import wraps


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

def escape(value):
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")\
        .replace(" ", "&nbsp;").replace('"', "&quot;").replace("\n", "<br/>")