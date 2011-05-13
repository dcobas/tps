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

if __name__ == '__main__':
    pass

