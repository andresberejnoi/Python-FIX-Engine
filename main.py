import fixapp
import argparse
import logging

def get_default_args():
    '''Returns a Namespace object mimicking the one created by created by parser.parse_args() method from the argparse library.
    It has common default values for testing but they can be easily changed on the returned object'''

    from types import SimpleNamespace

    args = {}
    args['config']  = ''
    args['verbose'] = 0
    args['plot']    = False
    args['plot_mode'] = 'candle'
    args['candle_width'] = '2S'
    args['plot_refresh_rate'] = 1000
    args['symbol'] = 'EUR/USD'
    args['interval'] = '4S'
    args['expert_advisor'] = 'rsi'

    args = SimpleNamespace(**args)

    return args

def main(args):
    app = fixapp.SessionAuto(args)
    app.start()

if __name__ == '__main__':
     #check arguments from commmand line and set everything up
     parser = argparse.ArgumentParser(description='FIX Client')
     parser.add_argument('--config', type=str, help='Name of configuration file')
     parser.add_argument('-v', '--verbose', action="count",
                         help="increase output verbosity (e.g., -vv is more than -v)")
     parser.add_argument('-p', '--plot', action='store_true')
     parser.add_argument('-pm','--plot_mode',default='candle',type=str,choices=['tick','candle'], help='Choose to make a price chart with tick data or with candlestick (OHLC) data. Candlestick mode will be more computationally intensive')
     parser.add_argument('-cw','--candle_width',default='2S',type=str,help='Width of each candle, in time')
     parser.add_argument('-prr','--plot_refresh_rate',default=1000,type=int,help='Refresh rate of the charting canvas, in milliseconds.')
     parser.add_argument('-s','--symbol',type=str,default='EUR/USD',help='The symbol of the securities for the trading algorithm to check')
     parser.add_argument('-i','--interval',type=str,default='4S',help='The symbol of the securities for the trading algorithm to check')
     parser.add_argument('-ea','--expert_advisor',type=str,default='rsi',help='Name for the expert advisor to use in the trading system')
     args = parser.parse_args()
     choices=['1S','2S','4S','10S','20S','30S','1T','2T','5T','10T']

     #-==========================================================================
     #-----Set the verbose level from commmand line and set up logging
     if args.verbose is None:
         VERBOSE_LEVEL = 0
     else:
         VERBOSE_LEVEL = args.verbose
     levels = [logging.ERROR,logging.WARNING,logging.INFO, logging.DEBUG]
     level = levels[min(len(levels)-1,VERBOSE_LEVEL)]  # get number to work with logging module

     logging.basicConfig(level=level,format='%(message)s')

     print(args)

     main(args)
