#!/usr/bin/env python3
from distutils.core import setup
from pip.req import parse_requirements
from pip.download import PipSession

install_requirements = parse_requirements("requirements.txt",
    session=PipSession())

setup(
    name="prophasis-core",
    description="Prophasis Monitoring Core",
    version="1.0",
    author="Cameron Gray",
    packages=["prophasis_core"],
    install_requires=[str(ir.req) for ir in install_requirements] + \
        ["prophasis_common"],
    package_data={"prophasis_core": ["classifier_functions.lua"]},
    entry_points={
        "console_scripts": [
            "prophasis-core = prophasis_core.core:main"
        ]
    }
)
