#!   /usr/bin/env   python
#    coding: utf8

class TpsException(Exception):
    pass

class TpsCritical(TpsException):
    """critical error, abort the whole test suite"""
    pass

class TpsError(TpsException):
    """error, continue remaining tests in test suite"""
    pass

class TpsUser(TpsException):
    """error, user intervention required"""
    pass

class TpsWarning(TpsException):
    """warning, a cautionary message should be displayed"""
    pass

class TpsInvalid(TpsException):
    """reserved: invalid parameters"""

class TpsNoBatch(TpsInvalid):
    """reserved: a suite was created without batch of tests to run"""
    pass

class TpsBadTestNo(TpsInvalid):
    """reserved: a bad test number was given"""
    pass

def raw_input(msg, default='y'):
    try:
        ret = __builtins__.raw_input(msg)
    except EOFError:
        return default
    return ret

if __name__ == '__main__':
    pass
