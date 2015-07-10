from os import path

from setuptools import setup


here = path.abspath(path.dirname(__file__))
# Get the long description from the relevant file
with open(path.join(here, "README.rst")) as f:
    long_description = f.read()

classifiers = ["License :: OSI Approved :: Apache Software License",
               "Topic :: Software Development :: Testing",
               "Operating System :: Microsoft :: Windows",
               "Operating System :: MacOS :: MacOS X"] + [
                  ("Programming Language :: Python :: %s" % x) for x in
                  "2.7".split()]


def main():
    setup(
        name="ptest",
        description="light testing framework for Python",
        long_description=long_description,
        version="1.1.0",
        keywords="test testing framework automation python",
        author="Karl Gong",
        author_email="karl.gong@outlook.com",
        url="https://github.com/KarlGong/ptest",
        license="Apache",
        entry_points={"console_scripts": ["ptest=ptest.main:main", ], },
        classifiers=classifiers,
        packages=["ptest"],
        package_data={"ptest": ["htmltemplate/*.*"]},
        zip_safe=False,
    )


if __name__ == "__main__":
    main()