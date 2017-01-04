from codecs import open
from os import path
import platform

from setuptools import setup

current_dir = path.abspath(path.dirname(__file__))
# Get the long description from the relevant file
with open(path.join(current_dir, "README.rst"), encoding="utf-8") as f:
    long_description = f.read()
with open(path.join(current_dir, "CHANGELOG"), encoding="utf-8") as f:
    long_description += "\n" + f.read()

classifiers = ["License :: OSI Approved :: Apache Software License",
               "Topic :: Software Development :: Testing",
               "Operating System :: Microsoft :: Windows",
               "Operating System :: MacOS :: MacOS X"] + [
                  ("Programming Language :: Python :: %s" % x) for x in
                  "2.7 3.4 3.5".split()]


def make_cmdline_entry_points():
    target = "ptest.main:main"
    entry_points = []
    version = platform.python_version()
    if version[0] == "2":
        entry_points.append("ptest=%s" % target)
    elif version[0] == "3":
        entry_points.append("ptest3=%s" % target)
    entry_points.append("ptest-%s=%s" % (version[:3], target))
    return entry_points


def main():
    setup(
        name="ptest",
        description="light test runner for Python",
        long_description=long_description,
        version="1.7.4",
        keywords="test testing framework automation python runner",
        author="Karl Gong",
        author_email="karl.gong@outlook.com",
        url="https://github.com/KarlGong/ptest",
        license="Apache",
        entry_points={
            "console_scripts": make_cmdline_entry_points(),
        },
        classifiers=classifiers,
        packages=["ptest"],
        package_data={"ptest": ["htmltemplate/*.*"]},
        zip_safe=False,
    )


if __name__ == "__main__":
    main()
