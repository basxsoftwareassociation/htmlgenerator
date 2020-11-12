from setuptools import find_packages, setup

setup(
    name="plisplate",
    version="0.1",
    description="Declarative HTML-focused templating system with lazy evaluation/rendering, for use in django",
    long_description="",
    url="https://basx.dev",
    author="basx Software Development Co., Ltd.",
    author_email="info@basx.dev",
    license="Private",
    install_requires=["django"],
    setup_requires=["setuptools_scm"],
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
)
