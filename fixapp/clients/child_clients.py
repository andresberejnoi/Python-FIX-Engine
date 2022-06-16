'''
Clients inherited from the base class and configured to particular counterparties
'''
__all__ = ['Tier1FXClient','FXPigClient', 'Tier1FXAuto']
import quickfix as fix
from .fix_clients import BaseFixClient, AutoFIXClient

class Tier1FXClient(BaseFixClient):
#lass Tier1FXClient(AutoFIXClient):

    def buy(self,**kargs):
        kargs['54'] = fix.Side_BUY
        msg = self._NewOrderSingle(kargs)
        msg.setField(fix.Account(self.settingsDic[self.TRADE_SESS.toString()].getString('Account')))
        self._record_json_order(msg,wanted_tags=[1,40,54,38,55,167])
        fix.Session.sendToTarget(msg,self.TRADE_SESS)
        #fix.Session.sendToTarget(msg, self.sessionID)

    def sell(self,**kargs):
        kargs['54'] = fix.Side_SELL
        msg = self._NewOrderSingle(kargs)
        msg.setField(fix.Account(self.settingsDic[self.TRADE_SESS.toString()].getString('Account')))
        self._record_json_order(msg,wanted_tags=[1,40,54,38,55,167])
        fix.Session.sendToTarget(msg, self.TRADE_SESS)

    def cancel_order(self, **kargs):
        msg = self._OrderCancelRequest(kargs, wanted_tags=[1,11,40,54,38,55,167])
        fix.Session.sendToTarget(msg,self.TRADE_SESS)


class Tier1FXAuto(AutoFIXClient):
    def buy(self,**kargs):
        kargs['54'] = fix.Side_BUY
        msg = self._NewOrderSingle(kargs)
        msg.setField(fix.Account(self.settingsDic[self.TRADE_SESS.toString()].getString('Account')))
        self._record_json_order(msg,wanted_tags=[1,40,54,38,55,167])
        fix.Session.sendToTarget(msg,self.TRADE_SESS)
        #fix.Session.sendToTarget(msg, self.sessionID)

    def sell(self,**kargs):
        kargs['54'] = fix.Side_SELL
        msg = self._NewOrderSingle(kargs)
        msg.setField(fix.Account(self.settingsDic[self.TRADE_SESS.toString()].getString('Account')))
        self._record_json_order(msg,wanted_tags=[1,40,54,38,55,167])
        fix.Session.sendToTarget(msg, self.TRADE_SESS)

    def cancel_order(self, **kargs):
        msg = self._OrderCancelRequest(kargs, wanted_tags=[1,11,40,54,38,55,167])
        fix.Session.sendToTarget(msg,self.TRADE_SESS)


class FXPigClient(BaseFixClient):
    def cancel_order(self,**kargs):
        msg = self._OrderCancelRequest(kargs,wanted_tags=[11,54,38,55,167])
        fix.Session.sendToTarget(msg, self.TRADE_SESS)


if __name__=='__main__':
    pass        #some basic tests can be included here
