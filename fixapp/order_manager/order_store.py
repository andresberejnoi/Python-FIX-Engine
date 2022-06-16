from fixapp.utils import print0, printv, printvv, printvvv

class OrderStore(object):
    '''
    Manage and keep track of buy and sell orders in the session
    '''
    def __init__(self):
        self.orders = []
        #self.ids    = []

    @property
    def get_ids(self):
        return [d['orderID'] for d in self.orders]

    def get_order(self,id):
        id_index = self.get_ids.index(id)
        return self.orders[id_index]

    def add_order(self, **kargs):
        _orderID = kargs['orderID']
        if self.isNotUnique(_orderID):
            printv('|xxx> Order with ID "{}" is not unique'.format(_orderID))
            return
        self.orders.append(kargs)
        printv("|===> Recorded order with ID: {}".format(_orderID))

    def get_last_order(self):
        return self.orders[-1]

    #Checkers
    def isNotUnique(self,id):
        if id in self.get_ids:
            return False
        return True
