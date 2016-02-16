#!/usr/bin/env python3
from distutils.core import setup
from pip.req import parse_requirements
from pip.download import PipSession

install_requirements = parse_requirements("requirements.txt",
    session=PipSession())

setup(
    name="prophasis-common",
    description="Prophasis Monitoring - Common Resources",
    version="1.0",
    author="Cameron Gray",
    packages=["prophasis_common"],
    install_requires=[str(ir.req) for ir in install_requirements],
    entry_points={
        "console_scripts": [
            "prophasis-common-setup = prophasis_common.setup_wizard:main"
        ]
    }
)
