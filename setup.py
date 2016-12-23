#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

import audio_device_controller


NAME = "audio_device_controller"
VERSION = str(audio_device_controller.VERSION)

with open("requirements.txt") as reqs_file:
    required = reqs_file.read().splitlines()

setup(
    name=NAME,
    version=VERSION,
    description="Audio device controller via HDMI CEC",
    author=["Javier Martinez"],
    author_email=["javi@flamingalah.net"],
    license="Apache 2.0",
    packages=find_packages(),
    scripts=["bin/audio_controller"],
    test_suite="nose.collector",
    requires=required,
    setup_requires=["nose>=1.0"],
)
