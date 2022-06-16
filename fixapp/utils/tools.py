__all__ = ['OHLC','OrderManager','OrderBook','FixDecoder','PairContainer','OrderedMessage',
           'TagPair','print_fix_string','unicode_fix','isSymbolTag']

from bs4 import BeautifulSoup as Soup     #to parse XML and other files
import sys
import quickfix44 as fix44
import quickfix as fix
import pandas as pd
import datetime as dt
from datetime import datetime
#from data_processing import create_ohlc_datapoint, ohlc_resample
from fixapp.data_manager import create_ohlc_datapoint, ohlc_resample
#from logging_redefinitions import *
#from fixapp.utils import print0,printv,printvv,printvvv
from . import print0,printv,printvv,printvvv
#import io
import os



class OHLC(object):
    '''OHLC -> Open, High, Low, Close'''
    #MIN_TIME_RESOLUTION = dt.timedelta(microseconds=1000)      #the minimum resolution will be 1 milisecond
    MIN_TIME_RESOLUTION = dt.timedelta(microseconds=1)

    def __init__(self,interval='1-Min'):
        self.openings    = []
        self.highs       = []
        self.lows        = []
        self.closings    = []
        self.timestamps  = []
        self.num_compressed_ticks = []          #for each entry write down how many ticks were used to generate it
        self.interval_str= interval
        self.INTERVAL    = None
        self.SYMBOL      = "SYM1/SYM2"

        #Use the variables below to keep track of beginning of new bars
        self.start_time  = None
        self.close_time  = None
        self.latest_time = None

    def __len__(self):
        return len(self.timestamps)

    def total_ticks(self):
        return sum(self.num_compressed_ticks)

    @classmethod
    def convert_str_to_microseconds(cls,str):
        length_of_time, timeframe = str.split('-')
        length_of_time = int(length_of_time)
        num_ticks = 1
        multiplier = 1             #this will be expressed in seconds

        if timeframe.lower() == 'micro':
            multiplier = 1
        if timeframe.lower() == 'milli':
            multiplier = 1000
        elif timeframe.lower() == 'sec':
            multiplier = 1000 * 1000
        elif timeframe.lower() == 'min':
            multiplier = 60 * 1000 * 1000
        elif timeframe.lower() == 'hour':
            multiplier = 60 * 60 * 1000 * 1000
        elif timeframe.lower() == 'day':
            multiplier = 24 * 60 * 60 * 1000 * 1000  #NOT CORRECT

        total_micro = multiplier * length_of_time * cls.MIN_TIME_RESOLUTION
        return total_micro

    @classmethod
    def convert_str_to_miliseconds(cls,str):
        '''convert everything to miliseconds datetime.timedelta object. This function is not correct'''
        length_of_time, timeframe = str.split('-')
        length_of_time = int(length_of_time)
        num_ticks = 1
        multiplier = 1             #this will be expressed in seconds

        if timeframe.lower() == 'milli':
            multiplier = 1
        elif timeframe.lower() == 'sec':
            multiplier = 1000
        elif timeframe.lower() == 'min':
            multiplier = 60 * 1000
        elif timeframe.lower() == 'hour':
            multiplier = 60 * 60 * 1000
        elif timeframe.lower() == 'day':
            multiplier = 24 * 60 * 60 * 1000   #completely correct since there aren't exactly 24 hours in a day

        total_milli = multiplier * length_of_time * cls.MIN_TIME_RESOLUTION
        return total_milli

    def update_start_time(self,new_time_str):
        self.start_time = self.create_datetime_object(new_time_str)

    def update_latest_time(self,new_time_str):
        self.latest_time = self.create_datetime_object(new_time_str)

    def isInterval_complete(self,latest_time):
        t1 = self.start_time
        t2 = self.create_datetime_object(latest_time)
        return (t2 - t1) > self.INTERVAL

    def update_timestamp_trackers(self):
        pass

    def create_datetime_object(self,date_time_str):
        '''For now I will just take into account the hour and seconds.
        This is made for data coming from Fortex in tag 52 in the format YYYYmmdd-HH:MM:SS:fff'''
        #intra_day_str = date_time_str.split('-')[-1]
        return dt.datetime.strptime(date_time_str, "%Y%m%d-%H:%M:%S.%f")

    def add_bar(self,*args):
        '''Bar tuple in args should contain:
        args[0] -> timestamp
        args[1] -> open price
        args[2] -> high price
        args[3] -> low price
        args[4] -> close price
        '''
        self.timestamps.append(args[0])
        self.openings.append(args[1])
        self.highs.append(args[2])
        self.lows.append(args[3])
        self.closings.append(args[4])
        self.num_compressed_ticks.append(args[5])

        printv("|=====> OHLC datapoint added. {} candles so far\n.".format(len(self)))

    def get_dataframe(self):
        data = pd.DataFrame({'symbol':self.SYMBOL,
                             'datetime':self.timestamps,
                             'open':self.openings,
                             'high':self.highs,
                             'low':self.lows,
                             'close':self.closings,
                             'ticks_compressed':self.num_compressed_ticks})

        return data

    def save_data(self,filename='candles.csv'):
        data = self.get_dataframe()
        data.to_csv(filename,index=False,sep=',')
        self.clear_ohlc_data()

    def clear_ohlc_data(self):
        self.timestamps.clear()
        self.openings.clear()
        self.highs.clear()
        self.lows.clear()
        self.num_compressed_ticks.clear()
        self.closings.clear()
        self.start_time  = None
        self.latest_time = None

class OrderManager(object):
    '''
    Manage and keep track of buy and sell orders in the session
    '''
    def __init__(self):
        self.open_order_ids = []        #sort of stack structure to store ids in order, but also it be accessed out of order
        self.history        = []        #chronological record of trades

    def get_last_open_order(self):
        return self.open_order_ids[-1]

    def remove_last_open_order(self):
        self.open_order_ids.pop()

    def pop_last_open_order(self):
        order_id = self.open_order_ids.pop()
        return order_id

    def add_order(self,id):
        self.open_order_ids.append(id)
        self.history.append(id)

    def remove_order(self,id):
        self.open_order_ids.remove(id)


    def close_order(self,id):
        pass

    #Checkers
    def isUnique(self,id):
        if id in self.history:
            return False
        return True

class OrderBook(object):
    '''Collects order book information from a session (for example, from a Data Market Refresh)'''
    iter_index = 0
    def __init__(self, interval='1-Min'):
        self.bids      = []
        self.asks      = []
        self.size_bids = []
        self.size_asks = []

        self.timestamp = []

        self.interval  = interval
        self.symbol    = None

    def add_bid(self,bid,size):
        self.bids.append(bid)
        self.size_bids.append(size)

    def add_ask(self,ask,size):
        self.asks.append(ask)
        self.size_asks.append(size)

    def add_timestamp(self,time_stamp):
        self.timestamp.append(time_stamp)

    def add_bid_offer(self,key,bid,offer):
        try:
            self.bid_offers[key] = [bid,offer]
        except KeyError as err:
            print(err)

    def clear_book(self):
        self.bids.clear()
        self.asks.clear()
        self.size_bids.clear()
        self.size_asks.clear()

    def save_ohlc_data(self):
        pass
    def save_book(self,output_file):
        data = pd.DataFrame({"Bid":self.bids,
                             "Size_bids":self.size_bids,
                             "Ask" :self.asks,
                             "Size_asks":self.size_asks,
                             "Time Sent":self.timestamp})

        output_name = datetime.utcnow().strftime("%Y%m%d-%H:%M:%S.%f")[:-3] + '.csv'
        data.to_csv(output_name,index=False,sep=',')
        printv("Market Data saved to {}".format(output_name))
        return output_name

    def plot(self):
        pass

    def __len__(self):
        return len(self.timestamp)

    def __iter__(self):
        return self

    def __next__(self):
        '''The schema of the data can change. For now I will keep it simple. Data will come as bid and ask'''
        i = self.iter_index

        t = self.timestamp[i]
        b = self.bids[i]
        a = self.asks[i]

        self.iter_index += 1

        return t,b,a


#===============================================================================
def get_any_tag(message, tag):
    '''general purpose tag value extractor'''
    try:
        val = message.getField(tag)
    except:
        try:
            val = message.getHeader.getField(tag)
        except:
            printv("Failed to read tag '{}' from message. Tag may be missing".format(tag))
            raise ValueError
    return val

class FixDecoder(object):
    """
    A Collection of tools to decode a FIX message. It will be based on the 4.4 version
    of the protocol, but later it could be improved to handle any version by using a data dictionary.
    The main goal is to be able to provide human-readable reports and feedback for debugging.
    """
    def __init__(self, datadictionary='FIX44.xml'):
        self.path_dict = datadictionary
        self.__build_dictionary()   #create the dictionary to store names read from the data dictionary
        self.orderbook = None

        #------data converters
        init_time = dt.datetime.utcnow()
        self.bid_ohlc  = OHLC(interval='20-Sec')
        self.ask_ohlc  = OHLC(interval='20-Sec')
        self.bid_ohlc.start_time = init_time
        self.ask_ohlc.start_time = init_time

        #Some definition dictionaries for clearer decoding. If it becomes too long, this class could be moved to a different file to avoid cluttering the client class
        self._ExecInst     =  {'tag':'18',
                              'G':'All or none',
                              'u':'Partial fill'}

        self._ExecType    =  {'tag':'150',
                              '0':'New',
                              '4':'Canceled',
                              '5':'Replaced',
                              '6':'Pending Cancel',
                              '8':'Rejected',
                              '9':'Suspended',
                              'E':'Pending Replace',
                              'F':'Trade (partial or fill)'}

        self._OrderStatus =  {'tag':'39',
                              '0':'New',
                              '1':'Partially Filled',
                              '2':'Filled',
                              '4':'Canceled',
                              '6':'Pending Canceled',
                              '8':'Rejected',
                              'E':'Pending Replace'}

        self._MDEntryType =  {'tag':'269',
                              '0':'Bid',
                              '1':'Offer',
                              '2':'Trade',
                              '3':'Index Value',
                              '4':'Opening Price',
                              '5':'Closing Price',
                              '6':'Settlement Price',
                              '7':'Trading Session High Price',
                              '8':'Trading Session Low Price',
                              '9':'Trading Session VWAP Price',
                              'A':'Imbalance',
                              'B':'Trade Volumne',
                              'C':'Open Interest'}
        self._CxlRejReason = {'tag':'102',
                              '0' : 'Too late to cancel',
                              '1' : 'Unknown order',
                              '2' : 'Broker / Exchange Option',
                              '3' : 'Order already in Pending Cancel or Pending Replace status',
                              '4' : 'Unable to process Order Mass Cancel Request <q>',
                              '5' : 'OrigOrdModTime <586> (586) did not match last TransactTime <60> (60) of order',
                              '6' : 'Duplicate ClOrdID <11> () received',
                              '99': 'Other'}

        self._CxlRejResponseTo = {'tag':'434',
                                  '1'  : 'Order Cancel Request <F>',
                                  '2' : 'Order Cancel/Replace Request <G>'}

    def __build_dictionary(self):
        '''This function was based on the one here: http://quickfix.13857.n7.nabble.com/MessageCracker-python-td6756.html'''
        self.datadict  = {}
        handler = open(self.path_dict).read()
        soup = Soup(handler,'xml')
        for s in soup.findAll('fields'):
            for m in s.findAll('field'):
                msg_attrs =m.attrs
                self.datadict[int(msg_attrs["number"])]=msg_attrs["name"]

    ''' ************************************************************************
    Operator Overloading
    '''
    def __getitem__(self,key):
        k = key
        if type(key) == str:
            k = int(key)

        return self.datadict[k]

    def __setitem__(self,key,value):
        k = key
        if type(key) == str:
            k = int(key)

        self.datadict[k] = value


    def keys(self):
        return self.datadict.keys()

    def items(self):
        return self.datadict.items()

    def values(self):
        return self.datadict.values()

    '''*************************************************************************
    Getters and Tools
    '''
    @staticmethod
    def get_MsgType(message):
        return message.getHeader().getField(35)

    def _get_MsgType(self, message):
        '''Return a string with the value of tag 35'''
        return message.getHeader().getField(35)     #35 is the tag for message type

    def _get_SendingTime(self,message):
        return message.getHeader().getField(52)

    def _get_error_report(self,message):
        '''return error data from a message containing the tag 35=3'''
        error_text    = message.getField(58)  #tag 58 usually contains an error messages
        reference_tag = message.getField(371) #tag 371 tells the tag number which is causing trouble
        ref_msg_type  = message.getField(372)
        return (error_text,reference_tag,ref_msg_type)

    def _get_text(self,message):
        try:
            return message.getField(58)     #tag 58 contains text, usually an error message
        except:
            return "No text tag (58) included"

    @staticmethod
    def get_any_tag(message, tag):
        '''general purpose tag value extractor'''
        try:
            val = message.getField(tag)
        except:
            try:
                val = message.getHeader().getField(tag)
            except:
                print("Failed to read tag '{}' from message".format(tag))
                return -1
        return val

    def search_tag_info(self,tag,print_to_file=False, dual_output=False):
        """
        tag => int or str representing the tag field. For Example, it can be tag=35
               or tag='35' or tag='MsgType'
        The tag value will be used to search for the definition online and print it
        or save it to a file.
        dual_output indicates if user wants both a file and console output. The parameter
        'print_to_file' takes precedence over this one, so if print_to_file==False,
        no file output will be created, even if dual_output == True
        """
        print("get_tag_info NOT IMPLEMENTED")

    def handler_MarketUpdate(self,message,datastream_ref):
        group = fix44.MarketDataSnapshotFullRefresh.NoMDEntries()

        num_entries = self.get_any_tag(message,268)   #tag 268 is the number of repeatting groups (NoMDEntries)
        timestamp   = self.get_any_tag(message,52)
        bid         = None
        ask         = None
        openint_bid = None
        openint_ask = None
        for i in range(int(num_entries)):
            #create the objects to hold the information from the message. If feels a little counter intuitive in Python, but at least it's working after trial and error
            md_entry_type = fix.MDEntryType()
            price         = fix.MDEntryPx()
            md_entry_size = fix.MDEntrySize()

            message.getGroup(i+1,group)     #group index starts at 1
            group.getField(md_entry_type)
            group.getField(price)
            group.getField(md_entry_size)

            #Extracting field values to strings
            t = p = s = -1
            try:
                t = md_entry_type.getValue()
                p = price.getValue()
                s = md_entry_size.getValue()
            except:
                pass
            if t=='0':          #it's a bid
                bid         = p
                openint_bid = s
            elif t=='1':        #it's an ask
                ask         = p
                openint_ask = s
        timestamp = create_datetime_object(timestamp)
        datastream_ref.add_tick(
            timestamp=timestamp,
            bid=bid,
            ask=ask,
            openinterest_bid=openint_bid,
            openinterest_ask=openint_ask,
        )

    def parse_MDRequestRefresh_for_data(self,message,num_entries):
        group = fix44.MarketDataSnapshotFullRefresh.NoMDEntries()
        try:
            timestamp = self.get_any_tag(message,52)
            self.bid_ohlc.SYMBOL = self.get_any_tag(message,55)
            self.ask_ohlc.SYMBOL = self.get_any_tag(message,55)

            # We check here if a bar is complete befofe collecting more data
            if self.bid_ohlc.isInterval_complete(timestamp):         #this conditional should work for both
                bid_bar = create_ohlc_datapoint(self.bid_ohlc.start_time,self.orderbook.bids)
                ask_bar = create_ohlc_datapoint(self.ask_ohlc.start_time,self.orderbook.asks)
                self.bid_ohlc.add_bar(*bid_bar,len(self.orderbook.bids))
                self.ask_ohlc.add_bar(*ask_bar,len(self.orderbook.asks))
                self.bid_ohlc.update_start_time(timestamp)
                self.ask_ohlc.update_start_time(timestamp)
                self.orderbook.clear_book()             #delete previous info
        except ValueError:
            print("Could not get tag 52")

        self.orderbook.add_timestamp(timestamp)
        for i in range(int(num_entries)):
            #create the objects to hold the information from the message. If feels a little counter intuitive in Python, but at least it's working after trial and error
            md_entry_type = fix.MDEntryType()
            price         = fix.MDEntryPx()
            md_entry_size = fix.MDEntrySize()

            message.getGroup(i+1,group)     #group index starts at 1
            group.getField(md_entry_type)
            group.getField(price)
            group.getField(md_entry_size)

            #Extracting field values to strings
            t = -1
            p = -1
            s = -1
            try:
                t = md_entry_type.getValue()
                p = price.getValue()
                s = md_entry_size.getValue()
            except:
                pass
            if t=='0':          #it's a bid
                self.orderbook.add_bid(p,s)
            elif t=='1':
                self.orderbook.add_ask(p,s)

    def parse_MDRequestRefresh_groups(self, message,num_entries):
        group = fix44.MarketDataSnapshotFullRefresh.NoMDEntries()
        printvv("{:<10}\t{:<10}\t{:<10}".format('Type','Size','Price'))
        for i in range(int(num_entries)):
            #create the objects to hold the information from the message. If feels a little counter intuitive in Python, but at least it's working after trial and error
            md_entry_type = fix.MDEntryType()
            price         = fix.MDEntryPx()
            md_entry_size = fix.MDEntrySize()

            message.getGroup(i+1,group)     #group index starts at 1
            group.getField(md_entry_type)
            group.getField(price)
            group.getField(md_entry_size)

            #Extracting field values to strings
            t = -1
            p = -1
            s = -1
            try:
                t = md_entry_type.getValue()
                p = price.getValue()
                s = md_entry_size.getValue()
                #s = ""
            except:
                pass

            if t=='0':          #it's a bid
                self.orderbook.add_bid(p,s)
            elif t=='1':
                self.orderbook.add_ask(p,s)

            printvv("{:<10}\t{:<10}\t{:<10}".format(self._MDEntryType[t],s,p))

        self.orderbook.add_timestamp(self._get_SendingTime(message)) #tag 52

    @staticmethod
    def get_FIX_dict(msg):
        '''returns a dictionary of the tags and values from a Quickfix message. '''
        msg_str = msg.toString()
        msg_dict = {}
        tag_value_pairs = msg_str.split('\x01')[:-1]
        #pairs = [p.split('=') for p in tag_value_pairs]
        #pairs = [(int(p[0]),p[1]) for p in pairs]
        for pair in tag_value_pairs:
            tag,val = pair.split('=')
            tag = int(tag)
            msg_dict.setdefault(tag, []).append(val)

        return msg_dict

    def format_wrapper(self, *args):
        #fmt_str = args[0].format(*args[1:])
        input_str = args[0]
        split_by_colon = input_str.split(':')  #separate the two sides of the string

        fmt_str = "{:<35} : {}".format(split_by_colon[0],split_by_colon[1])
        fmt_str = fmt_str.format(*args[1:])

        #fmt_str = "{:<35}:{}".format(*args)
        return fmt_str

    def extract_execution_report(message):
        execType            = self.get_any_tag(message,150)       #
        ord_status          = self.get_any_tag(message,39)        #tells if the order was executed
        quant_fillied       = self.get_any_tag(message,14)        #qunatity filled from the order
        quant_not_filled    = self.get_any_tag(message,151)
        exchange_rate       = self.get_any_tag(message,9329)
        commission          = self.get_any_tag(message,12)        #comission charged by broker on this trade
        orderID             = self.get_any_tag(message,37)
        return {'orderID':orderID,'execType':execType,'ord_status':ord_status,'quant_fillied':quant_fillied,
                'quant_not_filled':quant_not_filled,'exchange_rate':exchange_rate,'commission':commission}

    def extract_msg_data(self,msg_type,message):
        if msg_type == '8':
            self.extract_execution_report(message)
    def print_report(self,msg):

        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        #                REDEFINING PRINT FUNCTION HERE!!
        print = printvv

        #=======================================================================

        msg_type = self._get_MsgType(message)
        print('='*80)
        if msg_type == '0':
            print("HeartBeat (35='0')")
            pass   #a zero means a heartbeat

        elif msg_type == '3':   #
            error,ref_tag,ref_MsgType = self._get_error_report(message)
            #ref_MsgType = self.get_any_tag(372)     #the message type being referenced by the error
            print("Message rejected (35='3')")
            print(self.format_wrapper("Reference Tag (tag 371): {}",ref_tag))
            print(self.format_wrapper("Reference Message type (tag 372): {}",ref_MsgType))
            print(self.format_wrapper("Reason (tag 58):\n {}",self._get_text(message)))
            #print("Reference Tag (tag 371): {}".format(ref_tag))
            #print("Reference Message type (tag 372): {}".format(ref_MsgType))
            #print("reason (tag 58): {}".format(error))
            print()

        elif msg_type == '5':           #this is a logout message
            #print("Logout Message (35={})".format(msg_type))           #capturing this message. Now it is simply passing it but just uncomment if one wishing to print before logging out
            pass

        elif msg_type == '8':
            execType      = self.get_any_tag(message,150)       #
            ord_status    = self.get_any_tag(message,39)        #tells if the order was executed
            quant_fillied = self.get_any_tag(message,14)        #qunatity filled from the order
            not_filled    = self.get_any_tag(message,151)
            exchange_rate = self.get_any_tag(message,9329)
            commission    = self.get_any_tag(message,12)        #comission charged by broker on this trade

            print("Execution Report (35='{}')".format(msg_type))
            print(self.format_wrapper("Execution Type (tag 150): '{}' => {}", execType,self._ExecType[execType]))
            print(self.format_wrapper("Order Status (tag 39): '{}' => {}",ord_status,self._OrderStatus[ord_status]))
            print(self.format_wrapper("Quantity filled (tag 14): {}",quant_fillied))
            print(self.format_wrapper("Quantity NOT filled (tag 151): {}",not_filled))
            print(self.format_wrapper("USD Exchange rate (tag 9329): {}", exchange_rate))
            print(self.format_wrapper("Commission paid (tag 12): {}",commission))
            print(self.format_wrapper("Text (tag 58):\n {}",self._get_text(message)))
            print("\n")

        elif msg_type == '9':
            original_id       = self.get_any_tag(message,41)
            order_status      = self.get_any_tag(message,39)
            reject_reason     = self.get_any_tag(message,102)
            reject_responseTo = self.get_any_tag(message,434)
            id_by_broker      = self.get_any_tag(message,37)        #order id assigned by the broker
            ClOrdID           = self.get_any_tag(message,11)        #order id for client order getting rejected

            print("Order Cancel Reject (35={})".format(msg_type))
            print(self.format_wrapper("ID of order to be canceled: {}",original_id))
            print(self.format_wrapper("ID given by broker (tag 37): {}",id_by_broker))
            print(self.format_wrapper("ID of client order (ClOrdID tag 11): {}",ClOrdID))
            print(self.format_wrapper("Order Status (tag 39): '{}' => {}'",order_status,self._OrderStatus[order_status]))
            print(self.format_wrapper("Reject reason (tag 102): '{}' => {}",reject_reason,self._CxlRejReason[reject_reason]))
            print(self.format_wrapper("Reject ResponseTo (tag 434): '{}' => {}",reject_responseTo,self._CxlRejResponseTo[reject_responseTo]))
            print()

        elif msg_type == 'A':
            print("Logon Message (35='A')")

        elif msg_type == 'j':
            ref_MsgType        = self.get_any_tag(message,372)
            buss_reject_reason = self.get_any_tag(message,380)
            print("Allocation Instruction (35='j')")
            print(self.format_wrapper("Reference Message type (tag 372): {}",ref_MsgType))
            print(self.format_wrapper("Business Reject Reason (tag 380): {}",buss_reject_reason))
            print(self.format_wrapper("Reject Reason Explained:\n {}",self._get_text(message)))
            #print("Reference Message type (tag 372): {}".format(ref_MsgType))
            #print("Bpusiness Reject Reason (tag 380): {}".format(buss_reject_reason))
            #print("Reject Reason Explained: {}".format(self._get_text(message)))
            print()

        elif msg_type == 'P':
            alloc_status = self.get_any_tag(message,87)   #tag 87 is allocation status on a 35=P message
            text         = self._get_text(message)
            allocID      = self.get_any_tag(message,70)
            print("Allocation Inst Acknowledgement (35='{}') with ID: {}".format(msg_type,allocID))
            print(self.format_wrapper("Status: {}",alloc_status))
            print(self.format_wrapper("Text:\n {}",text))
            #print("Status: {}".format(alloc_status))
            #print("Text: {}".format(text))
            print()

        elif msg_type == 'V':   #market data requested
            print("Message (35='V')")
            print()

        elif msg_type == 'W':
            num_MDEntries = self.get_any_tag(message,268)   #tag 268 is the number of repeatting groups (NoMDEntries)
            _sending_time = self._get_SendingTime(message)
            print("Market Data Snapshot/Full Refresh (35={})".format(msg_type))
            #print(self.format_wrapper("SendingTime (tag 52): {}",_sending_time))
            #self.parse_MDRequestRefresh_groups(message,num_MDEntries)
            self.parse_MDRequestRefresh_for_data(message,num_MDEntries)

        elif msg_type == 'Y':
            print("Market Data Request Reject (35='{}')".format(msg_type))
            print(self.format_wrapper("Text:\n {}",self._get_text(message)))
            #print("Text: {}".format(self._get_text(message)))
            print()
        else:
            print("Message Type 35='{}' NOT IMPLEMENTED".format(msg_type))

#===============================================================================

'''
Simple scheme to adjust string:
- Convert Original Message to String
- Create pair classes for each tag/value pair
- Define the desired order
- arrange the message by putting the Pair objects based on their tags into a new list
- Add the remaining tags in whichever order one wants (make sure last one is always trailing tag)
- Create a Container class to hold all the arranged pairs
- Convert them to a string again with a class method
- convert the string into quickfix message, with a True value passed to respect the XML configuration file
- Check that message created actually corresponds to the message requirements
'''

class PairContainer(dict):
    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

    def __getitem__(self, key):
        val = dict.__getitem__(self, key)
        #print 'GET', key
        return val

    def __setitem__(self, key, val):
        #print 'SET', key, val
        dict.__setitem__(self, key, val)

    def __repr__(self):
        dictrepr = dict.__repr__(self)
        return '%s(%s)' % (type(self).__name__, dictrepr)

    def update(self, *args, **kwargs):
        #print 'update', args, kwargs
        for k, v in dict(*args, **kwargs).iteritems():
            self[k] = v


class OrderedMessage(object):
    def __init__(self,pair_objs, order=[8,9,35,49,56,34,52]):
        self.pairs     = pair_objs
        self.new_order = []
        self.order     = [str(tag) for tag in order]
        self.tags      = [pair.get_tag() for pair in pair_objs]   #this will preserve the original order
        self.dict      = {}                 #maps tags to the pair objects (this sounds so wrong on a performance level, but for now it is just a hack to test)

        print()
        for pair in pair_objs:
            self.dict.update(pair.get_dict())

    def arrange_pairs(self):

        #if no order is provided simply set self.new_order as self.pairs
        if len(self.order) == 0:
            self.new_order = self.pairs    #be careful. This is actually a reference to self.pairs, not a copy
            return


        num_fields = len(self.pairs)
        self.new_order = [None]*num_fields

        #First add all required header tags
        count_idx = 0
        for tag in self.order:
            try:
                #print("Tag inside TRY:",tag)
                pair = self.dict[tag]
                #print("PRINT IS:",pair)
                #self.new_order.append(pair)
                self.new_order[count_idx] = pair
                count_idx += 1
            except KeyError as err:
                print(err)
                print("'{}' is a required field in any message to Fortex FIX server".format(tag))
                exit(1)

        for tag in self.tags:
            if tag in self.order:
                continue            #we have already covered the required tags, so we can ignore them

            if tag == '10':
                pair = self.dict[tag]
                self.new_order[num_fields-1] = pair                #tag 10 is the checksum and always goes to the end
            else:
                self.new_order[count_idx] = self.dict[tag]
                count_idx += 1


    def toString(self):
        #arrange before converting
        self.arrange_pairs()
        print(self.new_order)
        str_msg = "\x01".join([pair.toString() for pair in self.new_order]) + '\x01'
        return str_msg

class TagPair(object):
    def __init__(self,tag_val_str):
        split_field = tag_val_str.split('=')
        split_field = [item.strip() for item in split_field]

        self.tag = split_field[0]
        self.val = split_field[1]
        #self.tag,self.val = [(tag.strip(),val.strip()) for tag,val in tag_val_str.split('=')]
        #self.tag,self.val = [[item.strip() for item in pair] for pair in  ]
        #self.tag = str(tag)
        #self.val = str(val)

    def toString(self):
        return str(self.tag) + '=' + str(self.val)
    def get_tag(self):
        return self.tag
    def get_val(self):
        return self.val
    def get_dict(self):
        return {self.tag:self}
    '''
    Overloading
    '''
    def __str__(self):
        return "{}={}".format(self.get_tag(),self.get_val())
    __repr__ = __str__

    def __lt__(self,other):
        if self.tag < other.tag:
            return True
        else:
            return False
    def __gt__(self,other):
        if self.tag > other.tag:
            return True
        else:
            return False

def print_fix_string(string):
    """Take string and replace characters FIX '|' characters to ones that appear correctly in the terminal and print it"""
    bar_in_unicode = '\x01'  # '|' from FIX messages in unicode
    new_str = string.replace(bar_in_unicode, '|')
    print(new_str)

def unicode_fix(string):
    """Take string and replace characters FIX '|' characters to ones that appear correctly in the terminal and return it"""
    bar_in_unicode = '\x01'  # '|' from FIX messages in unicode
    new_str = string.replace(bar_in_unicode, '|')
    return new_str

def isSymbolTag(tag):
    if tag == '55' or tag==55 or tag=='-55' or tag==-55:
        return True
    return False

def create_datetime_object(date_time_str):
    '''For now I will just take into account the hour and seconds.
    This is made for data coming from Fortex in tag 52 in the format YYYYmmdd-HH:MM:SS:fff'''
    #intra_day_str = date_time_str.split('-')[-1]
    val = date_time_str
    l = len(val)
    #assume string format is : '%Y%m%d %H:%M:%S.%f'
    #if str_format == '%Y%m%d %H:%M:%S.%f' and (l==21 or l==24):
    if l==21 or l==24:
        us = int(val[18:24])
        if l == 21:
            us *= 1000
        return dt.datetime(
            int(val[0:4]),
            int(val[4:6]),
            int(val[6:8]),
            int(val[9:11]),
            int(val[12:14]),
            int(val[15:17]),
            us)
    #return dt.datetime.strptime(date_time_str, "%Y%m%d-%H:%M:%S.%f")

def convert_str_to_microseconds(min_res,str):
    length_of_time, timeframe = str.split('-')
    length_of_time = int(length_of_time)
    num_ticks = 1
    multiplier = 1             #this will be expressed in seconds
    MIN_TIME_RESOLUTION = min_res

    if timeframe.lower() == 'micro':
        multiplier = 1
    elif timeframe.lower() == 'milli':
        multiplier = 1000
    elif timeframe.lower() == 'sec':
        multiplier = 1000 * 1000
    elif timeframe.lower() == 'min':
        multiplier = 60 * 1000 * 1000
    elif timeframe.lower() == 'hour':
        multiplier = 60 * 60 * 1000 * 1000
    elif timeframe.lower() == 'day':
        multiplier = 24 * 60 * 60 * 1000 * 1000  #NOT CORRECT

    total_micro = multiplier * length_of_time * MIN_TIME_RESOLUTION
    return total_micro



if __name__ == '__main__':
    pass            #possibly include some
