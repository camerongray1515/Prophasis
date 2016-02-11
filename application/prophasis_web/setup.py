#!/usr/bin/env python3
import os
from distutils.core import setup
from pip.req import parse_requirements
from pip.download import PipSession

install_requirements = parse_requirements("requirements.txt",
    session=PipSession())

# TODO: Recusively find all files in "templates" and "static" for use with
# package_data
setup(
    name="prophasis-web",
    description="Prophasis Monitoring Web Interface",
    version="1.0",
    author="Cameron Gray",
    packages=["prophasis_web"],
    install_requires=[str(ir.req) for ir in install_requirements] + \
        ["prophasis_common"],
    package_data={"prophasis_web": ["templates/*", "static/*"]},
    entry_points={
        "console_scripts": [
            "prophasis-web = prophasis_web.web:main"
        ]
    }
)
