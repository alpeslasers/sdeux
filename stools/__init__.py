# -*- coding: utf-8 -*-
"""
Initialize the logger

Created on March 31, 2020

Copyright Alpes Lasers SA, Neuchatel, Switzerland, 2020

@author: chiesa
"""
import logging
from pkg_resources import DistributionNotFound
import pkg_resources
from distutils.version import StrictVersion

pkg = "stools"
try:
    version = pkg_resources.get_distribution(pkg).version
    try:
        StrictVersion(version)
    except ValueError as e:
        version = 'devel'
except DistributionNotFound:
    version = "devel"

try:
    from logserviceclient.utils.logger import initLogger
    try:
        initLogger(pkg)
    except Exception:
        logging.warning("Log service client was not initialized properly")
except ImportError:
    pass
