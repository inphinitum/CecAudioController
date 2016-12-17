#!/usr/bin/env python3

from setuptools import setup

import cec_audio_controller


NAME = "cec_audio_controller"
VERSION = str(cec_audio_controller.VERSION)

with open("requirements.txt") as reqs_file:
    required = reqs_file.read().splitlines()

setup(
    name=NAME,
    version=VERSION,
    description="Audio device controller via HDMI CEC",
    author="Javier Martínez",
    author_email="javi@flamingalah.net",
    license="Apache 2.0",
    packages="cec_audio_controller",
    scripts="bin/audio_controller",
    test_suite="nose.collector",
    requires=required,
)
