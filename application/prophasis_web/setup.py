#!/usr/bin/env python3
import os
import re
from distutils.core import setup
from pip.req import parse_requirements
from pip.download import PipSession

install_requirements = parse_requirements("requirements.txt",
    session=PipSession())

def find_files(directory):
    found_files = []
    for root, subFolders, files in os.walk(directory):
        for filename in files:
            found_files.append(os.path.join(root, filename))
    return found_files

package_data_files = []
package_data_files += find_files("prophasis_web/static")
package_data_files += find_files("prophasis_web/templates")

setup(
    name="prophasis-web",
    description="Prophasis Monitoring Web Interface",
    version="1.0",
    author="Cameron Gray",
    packages=["prophasis_web"],
    install_requires=[str(ir.req) for ir in install_requirements] + \
        ["prophasis_common"],
    package_data={"prophasis_web": [
        re.sub("^prophasis_web/", "", f) for f in package_data_files]},
    entry_points={
        "console_scripts": [
            "prophasis-web = prophasis_web.web:main"
        ]
    },
    scripts = ["bin/prophasis-web-setup"]
)
