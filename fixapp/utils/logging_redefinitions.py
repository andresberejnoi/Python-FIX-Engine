"""
Here I am defining some functions to override the names in the logging module because they can be
confusing.
"""
__all__ = ['print0','printv','printvv','printvvv']

import logging

print0   = logging.error
printv   = logging.warning
printvv  = logging.info
printvvv = logging.debug
