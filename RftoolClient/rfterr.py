#!/usr/bin/env python3
# coding: utf-8


"""
rfterr.py
    - RftoolClient exception classes
"""


class RftoolClientError(Exception):
    """Base class for Rftool Client errors"""
    pass


class RftoolExecuteCommandError(RftoolClientError):
    """Exception thrown when rftool returns an error"""
    pass


class RftoolInterfaceError(RftoolClientError):
    """Rftool Interface error"""
    pass
