from setuptools import setup

classifiers = ['Development Status :: 2 - Pre-Alpha',
               'Intended Audience :: Developers',
               'License :: OSI Approved :: Apache Software License',
               'Operating System :: POSIX :: Linux',
               'Operating System :: Microsoft :: Windows',
               'Operating System :: MacOS :: MacOS X',
               'Topic :: Software Development :: Testing',
               'Topic :: Software Development :: Libraries',
               'Topic :: Utilities'] + [
                  ('Programming Language :: Python :: %s' % x) for x in
                  '2.7'.split()]


def main():
    setup(
        name="ptest",
        description="ptest: light testing framework for Python",
        version="0.0.1",
        keywords="test testing framework",
        platforms=['linux', 'win32'],
        author="Karl Gong",
        author_email="karl.gong@outlook.com",
        url="https://github.com/KarlGong/ptest",
        license="Apache",
        entry_points={"console_scripts": ['ptest=ptest:main', ], },
        classifiers=classifiers,
        packages=["_ptest"],
        package_data={"_ptest": ["htmltemplate/*.*"]},
        py_modules=["ptest"],
        zip_safe=False,
    )


if __name__ == "__main__":
    main()