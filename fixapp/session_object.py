import quickfix as fix
from fixapp import (FixDecoder, DataStream, OrderStore, Plotter, parse_fix_options, print0,printv,printvv,printvvv)
from fixapp import Tier1FXAuto as FixClient
from fixapp import ea
import datetime as dt
import time

def isTime(datastream):
    '''datastream: a DataStream object'''
    time_delta   = 10 * 1000000
    current_time = dt.datetime.utcnow()
    if current_time - datastream.last_accessed >= dt.timedelta(microseconds=time_delta):
        datastream.update_time(current_time)
        return True
    return False

class SessionAuto(object):
    actions_dict = {'b':'BUY','s':'SELL','h':'HOLD'}
    def __init__(self,args):
        self.args         = args
        self.config_file  = args.config
        self.settings     = fix.SessionSettings(self.config_file)
        self.decoder      = FixDecoder()
        self.datastream   = DataStream()
        self.orderstore   = OrderStore()
        self.app          = FixClient(self.datastream,self.decoder,self.orderstore,self.settings)
        self.storeFactory = fix.FileStoreFactory(self.settings)
        self.logFactory   = fix.FileLogFactory(self.settings)
        self.initiator    = fix.SocketInitiator(self.app,self.storeFactory,self.settings,self.logFactory)
        self.symbol       = args.symbol
        self.trader       = None
        self.interval     = args.interval
        if args.plot:
            self.plotter  = Plotter(self.datastream,args)
        else:
            self.plotter  = None
    def start(self):
        self.trader       = ea.get_advisor(self.args.expert_advisor)(self.datastream,self.interval)
        try:
            self.initiator.start()
            last_time = dt.datetime.utcnow()
            time.sleep(25)
            _, options = parse_fix_options("3 -55 {}".format(self.symbol))
            self.app.subscribe_to_data(**options)
            print("{:<27} {:<10} {:<10}".format('Datetime','Bid','Ask'))
            time.sleep(15)
            if self.args.plot:
                self.plotter.plot()
            while 1:
                if isTime(self.datastream):
                    action = self.trader.action()
                    printv("action to take: {}".format(self.actions_dict[action]))
                    if action == 'b':
                        _, options = parse_fix_options("1 -55 {}".format(self.symbol))
                        self.app.buy(**options)
                    elif action == 's':
                        _, options = parse_fix_options("2 -55 {}".format(self.symbol))
                        self.app.sell(**options)
                    elif action == 'h':
                        pass
                    else:
                        raise ValueError
        except (fix.ConfigError , fix.RuntimeError) as e:
            print(e)
