"""
Attempt to implement a FIX engine and see if it is possible.
Look at an example C++ client in the official repository:
https://github.com/quickfix/quickfix/blob/master/examples/tradeclient/Application.cpp
"""
__all__ = ['BaseFixClient','AutoFIXClient']
#import time
import datetime as dt
import quickfix as fix
import quickfix44 as fix44

from fixapp import print0, printv, printvv, printvvv, unicode_fix


class BaseFixClient(fix.Application):
    orderID = 0
    execID  = 0
    decoder = None      #create a FIX decoder instance as a class varaible for the application
    session_settings = None     #a reference to the session settings object
    settingsDic = {}
    session_ids = []
    TRADE_SESS  = None
    QUOTE_SESS  = None
    #Keep track of orders and IDs
    ORDERS_DICT   = {}
    LASTEST_ORDER = {}

    #Keep track of orders and ids
    open_subs   = []
    open_orders = []

    '''=========================================================================
    Internal message methdos
    '''


    def onCreate(self, sessionID):
        '''Improve this function later. Right now it expects exactly two sessions which contain specific strings'''
        num_sess = self.session_settings.size()
        if sessionID.toString().lower().find('quote') != -1:        #if the sessionID contains the word 'quote' we will assume it is a quote session
            self.QUOTE_SESS    = sessionID
        elif sessionID.toString().lower().find('trade') !=-1:       #if sessionID contains 'trade' we assume it is a trade session.
            self.TRADE_SESS = sessionID

        self.settingsDic[sessionID.toString()] = self.session_settings.get(sessionID)
        '''
        for i in range(num_sess):
            if sessionID.toString().lower().find('quote') != -1:        #if the sessionID contains the word 'quote' we will assume it is a quote session
        self.session_ids.append(sessionID)
        '''
        return


    def onLogon(self, sessionID):
        self.sessionID = sessionID
        #self.settingsDic = self.session_settings.get(sessionID)
        return


    def onLogout(self, sessionID):
        #fix.Session.lookupSession(sessionID).logout();
        return


    def toAdmin(self, message,sessionID):
        ##---Check if message is of logon

        #self.settingsDic = self.session_settings.get(sessionID)
        #username    = self.settingsDic[sessionID.toString()].getString('SenderCompID')
        msg_type    = message.getHeader().getField(fix.MsgType().getField())

        if msg_type == fix.MsgType_Logon:

            username = self.settingsDic[sessionID.toString()].getString('SenderCompID')
            password = self.settingsDic[sessionID.toString()].getString('Password')
            #username = sessionID.getSenderCompID().getValue()
            message.setField(fix.Username(username))
            message.setField(fix.Password(password))
        return


    def fromAdmin(self, message, sessionID):
        #print_fix_string("\nIncoming Msg (fromAdmin):\n"+message.toString())
        fix_str = unicode_fix(message.toString())
        self.decoder.print_report(message)
        return


    def toApp(self, message, sessionID):
        fix_str = unicode_fix(message.toString())
        return


    def fromApp(self, message, sessionID):
        '''Capture Messages coming from the counterparty'''
        fix_str = unicode_fix(message.toString())
        self.decoder.print_report(message)
        return


    def genOrderID(self):
    	self.orderID += 1
        #orderID = self.orderID
    	return str(self.orderID) + '-' + str(dt.datetime.timestamp(dt.datetime.utcnow()))


    def genExecID(self):
    	self.execID += 1
        #execID = self.execID
    	return str(self.execID) + '-' + str(dt.datetime.timestamp(dt.datetime.utcnow()))


    def _make_standard_header(self,sess_type):
        '''Make a standard header for Fortex FIX 4.4 Server based on their instruction file.
        A standard header for Fortex has the following tags (first 6 tags must be in this exact order):
        *     8  - BeginString  - required
        *     9  - BodyLength   - required
        *     35 - MsgType      - required
        *     49 - SenderCompID - required
        *     56 - TargetCompID - required
        *     34 - MsgSeqNum    - required
        *     43 - PossDupFlag  - Not required (can be Y or N)
        *     52 - SendingTime  - required
        '''
        #settingsDic = self.session_settings.get(self.sessionID)
        if sess_type.lower() == 'trade':
            sessionID = self.TRADE_SESS
        elif sess_type.lower() == 'quote':
            sessionID = self.QUOTE_SESS

        sender = self.settingsDic[sessionID.toString()].getString('SenderCompID')
        target = self.settingsDic[sessionID.toString()].getString('TargetCompID')
        msg = fix.Message()
        msg.getHeader().setField(fix.BeginString(fix.BeginString_FIX44))
        msg.getHeader().setField(fix.MsgType(fix.MsgType_Logon))
        msg.getHeader().setField(fix.SenderCompID(sender))
        msg.getHeader().setField(fix.TargetCompID(target))
        msg.getHeader().setField(fix.MsgSeqNum(3333))        #this is  a placeholder. I am just trying to force quickfix to put this tag in this particular order
        msg.getHeader().setField(fix.SendingTime(1))

        fix_str = unicode_fix(msg.toString())
        return msg


    '''===============================================================================
    Internally keep track of orders and subscriptions. (This might later be moved to an external class)
    '''


    def get_open_subscriptions(self):
        return self.open_subs


    def get_open_orders(self):
        return self.open_orders


    def get_last_subscription(self):
        return self.open_subs[-1]


    def get_last_order(self):
        return self.open_orders[-1]


    def close_subscription(self,id):
        self.open_subs.remove(id)


    def close_order(self,id):
        self.open_orders.remove(id)


    def add_subscription(self,id):
        self.open_subs.append(str(id))


    def add_order(self,id):
        self.open_orders.append(str(id))
        

    def _record_json_order(self, msg, wanted_tags=[1,40,54,38,55,167]):
        order_object = {}

        #For now I am going to store the entire message as a string
        order_object['raw_msg'] = msg.toString()

        for tag in wanted_tags:
            order_object[tag] = msg.getField(tag)

        id_tag   = 11    #tag for ClOrdID
        order_id = msg.getField(id_tag)
        order_object[id_tag] = order_id                   #store the id inside as well

        self.ORDERS_DICT[order_id] = order_object         #add to list of order info using the ID as key
        self.LASTEST_ORDER         = order_object         #remember the latest order for easier accessing
        printv("\n=====> Order recorded in memory with id = {}\n".format(order_id))

    
    def _retrieve_json_order(self, id):
        if id == -1 or id == '-1' or id == 'latest':
            return self.LASTEST_ORDER
        return self.ORDERS_DICT[id]

    
    '''=========================================================================
    Message Templates
    '''
    
    
    def __get_val(self,input_dict, tag, replace_with):
        '''Get values from user input and replace them if they are not present'''
        try:
            val = input_dict[tag]
        except KeyError:
            val = replace_with
        return val

    
    def _NewOrderSingle(self,kargs):
        '''
        _price       = kargs['44']          #Price
        _timeInForce = kargs['59']          #TimeInForce
        _orderQty    = kargs['38']          #OrderQty
        _asset       = kargs['55']          #Symbol
        _side        = kargs['43']          #Side
        _ordType     = kargs['40']          #OrdType
        _secType     = kargs['167']         #SecurityType
        '''
        _price       = float(self.__get_val(kargs,'44', 0))          #Price
        _asset       = kargs['55']                  #Symbol
        _timeInForce = self.__get_val(kargs,'59',fix.TimeInForce_FILL_OR_KILL)          #TimeInForce
        _orderQty    = float(self.__get_val(kargs,'38',10))          #OrderQty
        #_asset       = self.__get_val(kargs,'55','EUR/USD')          #Symbol
        _side        = self.__get_val(kargs,'54',fix.Side_BUY)          #Side tag 54
        _ordType     = self.__get_val(kargs,'40',fix.OrdType_MARKET)          #OrdType
        _secType     = self.__get_val(kargs,'167',fix.SecurityType_FOREIGN_EXCHANGE_CONTRACT)         #SecurityType

        msg = self._make_standard_header(sess_type='trade')
        msg.getHeader().setField(fix.BeginString(fix.BeginString_FIX44))
        msg.getHeader().setField(fix.MsgType(fix.MsgType_NewOrderSingle)) #35=D
        msg.setField(fix.ClOrdID(self.genOrderID()))                 #11=Unique order

        msg.setField(fix.TimeInForce(_timeInForce))   #-----> system complained of missing tag. This order is good for the day or for the session
        #print("--After ClOrdID")
        msg.setField(fix.SecurityType(_secType))         #-----> added because system complained about missing tag. instead of 'FOR' it could be fix.SecurityType_FOR. 'FOR' is for forex
        msg.setField(fix.HandlInst(fix.HandlInst_AUTOMATED_EXECUTION_ORDER_PRIVATE_NO_BROKER_INTERVENTION)) #21=3 (Manual order, best execution)
        msg.setField(fix.Symbol(_asset)) #55=SMBL ? the assest we wish to trade (e.g. 'EUR/USD', 'AAPL', 'SBUX', etc)
        msg.setField(fix.Side(_side))    #54=1 Buy
        msg.setField(fix.OrdType(_ordType)) #40=2 Limit order
        #print("--After OrdType")
        msg.setField(fix.OrderQty(_orderQty)) #38=100
        msg.setField(fix.Price(_price))          #tag 44 price
        #trade.setField(fix.TransactTime(int(dt.datetime.utcnow().strftime("%s"))))
        #print("--After Price")
        time_stamp = int(dt.datetime.timestamp(dt.datetime.utcnow()))
        #print(time_stamp)
        msg.getHeader().setField(fix.SendingTime(1))
        msg.setField(fix.StringField(60,(dt.datetime.utcnow().strftime("%Y%m%d-%H:%M:%S.%f"))[:-3]))

        return msg

    
    def _MarketDataRequest(self,kargs):
        '''
        _subscriptionType = kargs['263']   #SubscriptionRequestType 1 for subscription with updates, 2 is for unsubscribing
        _marketDepth      = kargs['264']   #MarketDepth
        _noMDEntryTypes   = kargs['267']  #NoMDEntryTypes
        _mdUpdateType     = kargs['265']   #MDUpdateType
        '''
        _subscriptionType = kargs['263']   #SubscriptionRequestType 1 for subscription with updates, 2 is for unsubscribing
        _marketDepth      = int(self.__get_val(kargs,'264',1))   #MarketDepth
        _noMDEntryTypes   = int(self.__get_val(kargs,'267',2))  #NoMDEntryTypes
        _mdUpdateType     = self.__get_val(kargs,'265',fix.MDUpdateType_FULL_REFRESH)   #MDUpdateType
        _asset            = self.__get_val(kargs,'55','EUR/USD')
        #_sub_ID           = self.__get_val(kargs,262,time.time())      #if no id is provided assume it is a new suscription and create new id

        quote = self._make_standard_header(sess_type='quote')
        quote.getHeader().setField(fix.MsgType(fix.MsgType_MarketDataRequest))

        quote.setField(fix.MDReqID(self.genExecID()))

        quote.setField(fix.SubscriptionRequestType(_subscriptionType))   #tag 263
        quote.setField(fix.MarketDepth(_marketDepth))      #tag 264. 0 -> Full Book and 1 -> Top of Book
        quote.setField(fix.NoMDEntryTypes(_noMDEntryTypes))       #tag 267  : 2 for bid and ask (I think)
        quote.setField(fix.MDUpdateType(_mdUpdateType))      #tag 265= '0' or '1' : 0 for full refresh

        group = fix44.MarketDataRequest().NoMDEntryTypes()
        group.setField(fix.MDEntryType(fix.MDEntryType_BID))
        quote.addGroup(group)
        group.setField(fix.MDEntryType(fix.MDEntryType_OFFER))
        quote.addGroup(group)

        quote.setField(fix.NoRelatedSym(1))     #tag 146
        symbol = fix44.MarketDataRequest().NoRelatedSym()
        symbol.setField(fix.Symbol(_asset))
        quote.addGroup(symbol)

        return quote

    
    def _OrderCancelRequest(self, kargs, wanted_tags=[11]):

        #----Extract keys
        _previous_id = self.__get_val(kargs,'41',-1)    #get id from previous order to cancel. If not provided default to the last one

        #----Retrieve order stored in memory or database
        order_object = self._retrieve_json_order(_previous_id)

        #----Create standard header
        msg = self._make_standard_header(sess_type='trade')
        msg.getHeader().setField(fix.MsgType(fix.MsgType_OrderCancelRequest))     #35 = F
        msg.setField(fix.ClOrdID(self.genOrderID()))                              #11=Unique order id

        #----Load data from previous order using the stringField method of Quickfix instead of calling by specific tag names
        for tag in wanted_tags:
            value = order_object[tag]
            if tag == 11 or tag == '11':                              #we change 11 to 41 because 11 will be used for this order's id, while 41 is the id of the order we want to cancel
                tag = fix.OrigClOrdID().getField()                    #Get the tag number (it should be 41 but this is more resistant to changes in protocol)
            msg.setField(fix.StringField(tag,value))

        #----Add transaction time
        msg.setField(fix.StringField(60,(dt.datetime.utcnow().strftime("%Y%m%d-%H:%M:%S.%f"))[:-3]))    #60 = transaction time

        return msg

    
    def _OrderStatusRequest(self,kargs):

        _side = self.__get_val(kargs,'54',fix.Side_BUY)#----Extract keys
        _previous_id = self.__get_val(kargs,'41',-1)    #get id from previous order to cancel. If not provided default to the last one

        msg = self._make_standard_header(sess_type='trade')
        msg.getHeader().setField(fix.MsgType(fix.MsgType_OrderStatusRequest))       #35 = H
        msg.setField(fix.ClOrdID(_previous_id))                                              # 11 = order id
        msg.setField(fix.Side(_side))

        return msg

    
    
    '''=========================================================================
    Tools and useful functions
    '''
   
   
    def has_quote_session(self):
        '''checks if there is a quote session available'''
        if self.QUOTE_SESS is not None:
            return True
        return False
    
    
    def has_trade_session(self):
        if self.TRADE_SESS is not None:
            return True
        return False

    
    def has_data_to_save(self):
        if (len(self.decoder.bid_ohlc) > 1) or (len(self.decoder.ask_ohlc) > 1):
            return True

        return False

    
    '''=========================================================================
    User interface
    '''
    
    
    def buy(self,**kargs):
        kargs['54'] = fix.Side_BUY
        msg = self._NewOrderSingle(kargs)
        #msg.setField(fix.Account(self.settingsDic.getString('Account')))
        self._record_json_order(msg,wanted_tags=[40,54,38,55,167])
        fix.Session.sendToTarget(msg, self.TRADE_SESS)
        #fix.Session.sendToTarget(msg,self.sessionID)

    
    def sell(self,**kargs):
        kargs['54'] = fix.Side_SELL
        msg = self._NewOrderSingle(kargs)
        #msg.setField(fix.Account(self.settingsDic.getString('Account')))
        self._record_json_order(msg,wanted_tags=[40,54,38,55,167])
        fix.Session.sendToTarget(msg, self.TRADE_SESS)
        #fix.Session.sendToTarget(msg,self.sessionID)

    
    def limit_buy(self, **kargs):
        kargs['40'] = fix.OrdType_LIMIT
        kargs['54'] = fix.Side_BUY
        msg = self._NewOrderSingle(kargs)

        self._record_json_order(msg,wanted_tags=[40,54,38,55,167])
        fix.Sessions.sendToTarget(msg,self.TRADE_SESS)
        #fix.Session.sendToTarget(msg,self.sessionID)

    
    def limit_sell(self, **kargs):
        kargs['40'] = fix.OrdType_LIMIT
        kargs['54'] = fix.Side_SELL
        msg = self._NewOrderSingle(kargs)

        self._record_json_order(msg,wanted_tags=[40,54,38,55,167])
        fix.Sessions.sendToTarget(msg,self.TRADE_SESS)
        #fix.Session.sendToTarget(msg,self.sessionID)

    
    def cancel_order(self,**kargs):
        msg = self._OrderCancelRequest(kargs,wanted_tags=[11,40,54,38,55,167])
        fix.Session.sendToTarget(msg, self.TRADE_SESS)

    
    def check_order_status(self,**kargs):
        msg = self._OrderStatusRequest(kargs)
        fix.Session.sendToTarget(msg,self.TRADE_SESS)
        #fix.Session.sendToTarget(msg,self.sessionID)

    
    def subscribe_to_data(self,**kargs):
        kargs['263'] = fix.SubscriptionRequestType_SNAPSHOT_PLUS_UPDATES
        msg = self._MarketDataRequest(kargs)
        fix.Session.sendToTarget(msg, self.QUOTE_SESS)
        #fix.Session.sendToTarget(msg,self.sessionID)

    
    def unsubscribe_to_data(self,**kargs):
        kargs['263'] = fix.SubscriptionRequestType_DISABLE_PREVIOUS_SNAPSHOT_PLUS_UPDATE_REQUEST
        msg = self._MarketDataRequest(kargs)
        fix.Session.sendToTarget(msg, self.QUOTE_SESS)
        #fix.Session.sendToTarget(msg,self.sessionID)

    
    def logout(self):
        msg = fix.Message()
        msg.getHeader().setField(fix.BeginString(fix.BeginString_FIX44))
        msg.getHeader().setField(fix.MsgType(fix.MsgType_Logout))

        fix.Session.sendToTarget(msg, self.TRADE_SESS)
        fix.Session.sendToTarget(msg,self.QUOTE_SESS)
        #fix.Session.sendToTarget(msg,self.sessionID)

    
    def test_message(self):
        trade = self._make_standard_header()
        trade.setField(fix.SecurityType('FOR'))         #-----> added because system complained about missing tag. instead of 'FOR' it could be fix.SecurityType_FOR. 'FOR' is for forex
        trade.setField(fix.TimeInForce(fix.TimeInForce_GOOD_TILL_CANCEL))   #-----> system complained of missing tag. This order is good for the day or for the session
        #print("--After ClOrdID")
        trade.setField(fix.HandlInst(fix.HandlInst_AUTOMATED_EXECUTION_ORDER_PRIVATE_NO_BROKER_INTERVENTION)) #21=3 (Manual order, best execution)
        trade.setField(fix.Symbol('EUR/USD')) #55=SMBL ? the assest we wish to trade (e.g. 'EUR/USD', 'AAPL', 'SBUX', etc)
        trade.setField(fix.Side(fix.Side_BUY)) #43=1 Buy
        trade.setField(fix.OrdType(fix.OrdType_MARKET)) #40=2 Limit order
        #print("--After OrdType")
        trade.setField(fix.OrderQty(10)) #38=100

        str_msg = trade.toString()
        return trade


class AutoFIXClient(BaseFixClient):
    
    
    def __init__(self,datastream,decoder,orderStore,session_settings):
        super(AutoFIXClient,self).__init__()
        self.datastream       = datastream
        self.decoder          = decoder
        self.orderStore      = orderStore
        self.session_settings = session_settings
        self.check_interval   = '5S'

    
    def fromAdmin(self, message, sessionID):
        #print_fix_string("\nIncoming Msg (fromAdmin):\n"+message.toString())
        fix_str = unicode_fix(message.toString())
        printvv("\nIncoming Msg (fromAdmin):\n{}".format(fix_str))
        #msg_type = self.decoder.get_any_tag(message,35)
        return

    
    def fromApp(self, message, sessionID):
        '''Capture Messages coming from the counterparty'''
        fix_str = unicode_fix(message.toString())
        printvv("\nFROM APP:\n{}".format(fix_str))
        #d = self.decoder.get_FIX_dict(message)
        msg_type = self.decoder.get_any_tag(message,35)
        if msg_type == 'W':
            self.decoder.handler_MarketUpdate(message,self.datastream)
        elif msg_type == '8':   #this is an execution report for an order
            order_info = self.decoder.extract_execution_report(message)
            self.orderStore.add_order(**order_info)
        return


if __name__ == '__main__':
    pass