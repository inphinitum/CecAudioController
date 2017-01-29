#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import audio_device_controller

from setuptools import setup, find_packages


with open("requirements.txt") as reqs_file:
    required = reqs_file.read().splitlines()

NAME = "audio_device_controller"
VERSION = str(audio_device_controller.VERSION)

setup(
    name=NAME,
    version=VERSION,
    description="Audio device controller via different protocols such as HDMI CEC",
    author="Javier Martinez",
    author_email="javi@flamingalah.net",
    license="GPLv2",
    url="https://github.com/inphinitum/audio-device-controller",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "audio-device-controller = audio_device_controller.audiodevcontroller:entry",
        ],
    },
    test_suite="nose.collector",
    requires=required,
    setup_requires=["nose>=1.0"],
    classifiers=["Development Status :: 3 - Alpha",
                 "Programming Language :: Python 3.3",
                 "Programming Language :: Python 3.4",
                 "Programming Language :: Python 3.5"]
)
