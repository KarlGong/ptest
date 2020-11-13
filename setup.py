import platform
from os import path

from setuptools import setup

from ptest import __version__

current_dir = path.abspath(path.dirname(__file__))
# Get the long description from the relevant file
with open(path.join(current_dir, "README.md"), encoding="utf-8") as f:
    long_description = f.read()
with open(path.join(current_dir, "CHANGELOG"), encoding="utf-8") as f:
    long_description += "\n" + f.read()

classifiers = ["License :: OSI Approved :: Apache Software License",
               "Topic :: Software Development :: Testing",
               "Operating System :: Microsoft :: Windows",
               "Operating System :: MacOS :: MacOS X"] + \
              [("Programming Language :: Python :: %s" % x) for x in "3.6 3.7 3.8 3.9".split()]


def make_cmdline_entry_points():
    target = "ptest.main:main"
    entry_points = []
    version = platform.python_version()
    entry_points.append("ptest=%s" % target)
    entry_points.append("ptest3=%s" % target)
    entry_points.append("ptest-%s=%s" % (version[:3], target))
    return entry_points


def main():
    setup(
        name="ptest",
        description="light test framework for Python",
        long_description=long_description,
        long_description_content_type="text/markdown",
        version=__version__,
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
        python_requires=">=3.6",
        zip_safe=False,
    )


if __name__ == "__main__":
    main()
