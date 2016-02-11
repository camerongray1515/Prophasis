#!/usr/bin/env python3
from distutils.core import setup
from pip.req import parse_requirements
from pip.download import PipSession

install_requirements = parse_requirements("requirements.txt",
    session=PipSession())

setup(
    name="prophasis-agent",
    description="Prophasis Monitoring Agent",
    version="1.0",
    author="Cameron Gray",
    packages=["prophasis_agent"],
    install_requires=[str(ir.req) for ir in install_requirements],
    entry_points={
        "console_scripts": [
            "prophasis-agent = prophasis_agent.agent:main"
        ]
    }
)
