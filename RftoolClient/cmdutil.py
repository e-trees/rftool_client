#!/usr/bin/env python3
# coding: utf-8


"""
cmdutil.py
    - Command server parsing utilities
"""


class CmdUtil:
    @classmethod
    def joinargs(cls, cmdstr, cmdargs):
        return " ".join([cmdstr, " ".join([str(arg) for arg in cmdargs])])

    @classmethod
    def splitargs(cls, resstr):
        ret = []
        str_args = resstr.split()[1:]
        for str_arg in str_args:
            try:
                if "." in str_arg:
                    ret.append(float(str_arg))
                else:
                    ret.append(int(str_arg))
            except ValueError:
                ret.append(str_arg)
        return ret
    
    @classmethod
    def split_response(cls, resstr, delimiter):
        ret = []
        str_resps = resstr.split(delimiter)
        for str_resp in str_resps:
            try:
                if "." in str_resp:
                    ret.append(float(str_resp))
                else:
                    ret.append(int(str_resp))
            except ValueError:
                ret.append(str_resp)
        return ret