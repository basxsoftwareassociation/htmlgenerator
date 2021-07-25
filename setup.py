from setuptools import Extension, find_packages, setup

with open("README.md") as f:
    long_description = f.read()

with open("htmlgenerator/__init__.pyx") as f:
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
            Extension("htmlgenerator", ["htmlgenerator/__init__.pyx"]),
            Extension("htmlgenerator.base", ["htmlgenerator/base.pyx"]),
            Extension("htmlgenerator.htmltags", ["htmlgenerator/htmltags.pyx"]),
            Extension("htmlgenerator.lazy", ["htmlgenerator/lazy.pyx"]),
            Extension("htmlgenerator.safestring", ["htmlgenerator/safestring.pyx"]),
        ],
        language_level=3,
    )
except ImportError:
    extensions = [
        Extension("htmlgenerator", ["htmlgenerator/__init__.c"]),
        Extension("htmlgenerator.base", ["htmlgenerator/base.c"]),
        Extension("htmlgenerator.htmltags", ["htmlgenerator/htmltags.c"]),
        Extension("htmlgenerator.lazy", ["htmlgenerator/lazy.c"]),
        Extension("htmlgenerator.safestring", ["htmlgenerator/safestring.c"]),
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
    packages=find_packages(),
    ext_modules=extensions,
    zip_safe=False,
    include_package_data=True,
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
