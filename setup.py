from setuptools import Extension, setup

with open("README.md") as f:
    long_description = f.read()

with open("htmlgenerator.pyx") as f:
    # magic n stuff
    version = (
        [i for i in f.readlines() if "__version__" in i][-1]
        .split("=", 1)[1]
        .strip()
        .strip('"')
    )


try:
    from Cython.Build import cythonize

    extensions = cythonize(
        [
            Extension("htmlgenerator", ["htmlgenerator.pyx"]),
        ],
        language_level=3,
        annotate=True,
    )
except ImportError:
    extensions = [
        Extension("htmlgenerator", ["htmlgenerator.c"]),
    ]


setup(
    name="htmlgenerator",
    description="Declarative HTML templating system with lazy rendering",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/basxsoftwareassociation/htmlgenerator",
    author="basx Software Association",
    author_email="sam@basx.dev",
    version=version,
    license="New BSD License",
    zip_safe=False,
    include_package_data=True,
    ext_modules=extensions,
    extras_require={"all": ["black", "beautifulsoup4", "lxml"]},
    entry_points={
        "console_scripts": [
            "convertfromhtml = htmlgenerator.contrib.convertfromhtml:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
    ],
)
