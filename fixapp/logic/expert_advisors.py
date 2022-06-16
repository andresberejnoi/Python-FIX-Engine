"""Use technical indicators to make decisions"""
from . import ta
import sys, inspect
#from logging_redefinitions import *
from fixapp import print0, printv, printvv, printvvv

def print_classes():
    is_class_member = lambda member: inspect.isclass(member) and member.__module__ == __name__
    clsmembers = inspect.getmembers(sys.modules[__name__], is_class_member)

    class_names = [n[0] for n in clsmembers]
    print(class_names)

def get_advisor(name):
    thismodule = sys.modules[__name__]
    allowed_names = {n.lower():n for n in ta.__list_indicators()}
    n = name.lower()
    try:
        expert_name = allowed_names[n]
        expert_obj = getattr(thismodule,expert_name,None)      #this will return None if func_name is not found in module
    except KeyError:
        return None
    return expert_obj

def factory_expert_advisor(id,*args):
    pass

class Base_EA(object):
    def __init__(self,indic_id,datastream,interval):
        self.indicator_func = ta.get_indicator(indic_id)
        self.datastream     = datastream
        self.interval       = interval

    def has_enough_datapoints(self,n):
        '''make sure the dataframe has enough datapoints to complete the computation.
        i.e. for a small moving average for 50 candles, we need at least 50 candles in the dataframe'''
        if len(self.datastream) >= n:
            return True
        else:
            return False

    def action(self):
        pass #override this depending on the indicator

class RSI(Base_EA):
    def __init__(self,datastream,interval):
        super().__init__('rsi',datastream,interval)

    def action(self,n=14):
        "returns 'b' for buy, 's' for sell, or 'h' for hold/wait"
        if self.has_enough_datapoints(n):
            data = self.datastream.get_ohlc(self.interval)
            data = self.indicator_func(data['bid'],n)
            data *= 100
        else:
            printvvv("not enough datapoints clause")
            return 'h'

        try:
            last_point = data.iat[-1]       #get last element
        except KeyError:
            printvvv("except clause")
            return 'h'

        printv('RSI is: {}'.format(last_point))
        if last_point < 30:
            return 'b'
        elif last_point > 70:
            return 's'   #we should check that there is a position to sell
        else:
            return 'h'

class Base_SMA(Base_EA):
    NUM_BARS = 50
    def next(self):
        pass

class SMA50(Base_SMA):
    NUM_BARS = 50

class SMA100(Base_SMA):
    NUM_BARS = 100

class SMA200(Base_SMA):
    NUM_BARS = 200
