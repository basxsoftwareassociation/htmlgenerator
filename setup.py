from setuptools import find_packages, setup

with open("README.md") as f:
    long_description = f.read()

setup(
    name="htmlgenerator",
    description="Declarative HTML templating system with lazy rendering",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/basxsoftwareassociation/htmlgenerator",
    author="basx Software Association",
    author_email="sam@basx.dev",
    license="New BSD License",
    install_requires=[],
    setup_requires=["setuptools_autover"],
    use_autover={
        "root_version": "0.2",
        "parse_tag": lambda tag: tag.lstrip("v"),
        "create_version": lambda ver: "{}.{}".format(
            getattr(ver, "latest_release"), ver.distance
        ),
    },
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
    ],
)
