import datetime as dt
import pandas as pd
from fixapp.utils import print0,printv,printvv,printvvv
from . import ohlc_resample

class DataStream():
    '''Replacement for OrderBook and should be in a higher level location.'''
    ITER_IDX = 0
    MEANING_DICT = {
        't'  : 'datetime',
        'b'  : 'bid',
        'a'  : 'ask',
        'vb' : 'volume bid',
        'va' : 'volume ask',
        'ob' : 'open interest bid',
        'oa' : 'open interest ask',
        'sym': 'asset symbol (i.e. EUR/USD)'
    }
    def __init__(self):
        self.symbol           = ""
        self.timestamps       = []
        self.bids             = []
        self.asks             = []
        self.volume_bid       = []
        self.volume_ask       = []
        self.openinterest_bid = []
        self.openinterest_ask = []

        self.last_checked     = dt.datetime.utcnow()

    @property
    def last_accessed(self):
        return self.last_checked

    def update_time(self,new_time):
        self.last_checked = new_time

    def __len__(self):
        return len(self.timestamps)

    def __iter__(self):
        return self

    def __next__(self):
        i = self.ITER_IDX
        #Check for a stopping condition
        if i >= len(self):
            raise StopIteration()
        else:
            tick = self.get_tick(idx=i)
            self.ITER_IDX += 1
            return tick

    def get_tick(self,idx=None,tick_format=['t','b','a']):
        '''always returns the latest tick data available.
        format tells the function what information to pack for return. For example,
        the default format is [t,b,a] which tells the program to return timestamp, bid, and ask.
        possible values are:
        t  -> timestamp
        b  -> bid
        a  -> ask
        vb -> volume bid
        va -> volume ask
        ob -> open interest bid
        oa -> open interest ask
        '''
        #Define the correct index to use
        if idx is None:
            i = -1
        else:
            i = idx
        output_tick = []
        for requested_data in tick_format:
            if requested_data.lower()   == 't':
                output_tick.append(self.timestamps[i])
            elif requested_data.lower() == 'b':
                output_tick.append(self.bids[i])
            elif requested_data.lower() == 'a':
                output_tick.append(self.asks[i])
            elif requested_data.lower() == 'vb':
                output_tick.append(self.volume_bid[i])
            elif requested_data.lower() == 'va':
                output_tick.append(self.volume_ask[i])
            elif requested_data.lower() == 'ob':
                output_tick.append(self.open_interest_bid[i])
            elif requested_data.lower() == 'oa':
                output_tick.append(self.open_interest_ask[i])
            elif requested_data.lower() == 'sym':
                output_tick.append(self.symbol)
        return output_tick

    def get_tick_in_ohlc(self,idx=None,tick_format=['t','b']):
        '''return the tick data repeated for open, high, low and close. if format has 'b'
        then the bid price will be repeated but if it has 'a' then the ask price will.'''
        tick = self.get_tick(idx=idx,tick_format=tick_format)
        ohlc_tick = []
        #shape in in OHLC format
        ohlc_tick = [tick[1]] * 4    #take the price and repeat it for open, high, low, close.
        ohlc_tick = [tick[0]] + ohlc_tick    #add the timestamp

        return ohlc_tick
    def _prefill_kargs(self,kargs_dict):
        keys = ['timestamp','bid','ask','volume_bid','volume_ask','openinterest_bid','openinterest_ask']
        for k in keys:
            try:
                kargs_dict[k]
            except KeyError:
                kargs_dict[k] = -1

        return kargs_dict

    def add_tick(self,**kargs):
        kargs = self._prefill_kargs(kargs)
        bid         = kargs['bid']
        ask         = kargs['ask']
        timestamp   = kargs['timestamp']
        openint_bid = kargs['openinterest_bid']
        openint_ask = kargs['openinterest_ask']

        self.timestamps.append(timestamp)
        self.bids.append(bid)
        self.asks.append(ask)
        self.openinterest_bid.append(openint_bid)
        self.openinterest_ask.append(openint_ask)
        print("----->tick added")
        try:
            printvv("{:<27} {:<10} {:<10}".format(str(self.timestamps[-1]),str(self.bids[-1]),str(self.asks[-1])))
        except TypeError:
            printvv("-----error------")

    def get_dataframe(self,size=-1,empty_data=False,include_cols=['t','b','a']):
        '''size indicates how many rows to include in the dataframe, counting from the last row up.
        empty_data is a flag to see if we should clear all the rows included in the dataframe'''
        if (len(self) < size) or (size < 0):
            start_idx = 0
        else:
            start_idx = len(self) - size
        data = {
            'datetime':self.timestamps[start_idx:],
            'bid'     :self.bids[start_idx:],
            'ask'     :self.asks[start_idx:],
        }
        df = pd.DataFrame(data)
        return df

    def get_json_ticks(self,size=200,empty_data=False,include_cols=['t','b','a'],use_midprice=False):
        df = self.get_dataframe(size=size,include_cols=include_cols)
        if use_midprice:
            df['price'] = df[['ask', 'bid']].mean(axis=1)
            return df[['datetime','price']].to_dict(orient="list")
        else:
            #For now I will return the ask price by default. Maybe I could return both
            df['price'] = df['ask']
            return df[['datetime','price']].to_dict(orient="list")

    def get_json_ohlc(self,timeframe,size=200,empty_data=False,include_cols=['t','b','a'], use_midprice=False):
        '''This will take a lot longer since we are taking a dataframe and performing a resampling operation.
        Maybe this could be done in the front-end side to avoid all these computations'''
        ohlc_df = self.get_ohlc(timeframe=timeframe,num_bars=size)
        ohlc_df = ohlc_df['ask']
        return ohlc_df.to_json()

    def get_ohlc(self,timeframe,num_bars=-1):
        data = self.get_dataframe(size=num_bars)#size=num_bars)
        bid_ask_ohlc = ohlc_resample(data,timeframe)
        return bid_ask_ohlc

    def clear_all_data(self):
        self.symbol = ""
        self.timestamps.clear()
        self.bids.clear()
        self.asks.clear()
        self.volume_bid.clear()
        self.volume_ask.clear()
        self.open_interest_bid.clear()
        self.open_interest_ask.clear()
