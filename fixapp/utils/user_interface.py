
__all__ = ['fix_started_msg','set_asset_name','parse_fix_options']


def fix_started_msg():
    print()
    print("FIX application has started...")
    print("Enter an action to perform:")
    print("*\t1 -> Place Buy Order")
    print("*\t2 -> Place Sell Order")
    print("*\t3 -> Subscribe to Market Data")
    print("*\t4 -> Cancel Market Data Subscription")
    print("*\t5 -> Order Cancel Request")
    print("*\t6 -> Order Status Request")
    print()
    print("*\tlogout -> Logout and Exit")
    print("*\td -> Start debugger")
    print()

def set_asset_name(curr1, *args):
    """
    Join asset names or currencies. For example, to trade EUR/USD, simply
    do (curr1='EUR', curr2='USD', sep='/', extension='').

    If the asset name already comes formatet then just put it all in curr1. For example:
    if we receive EURUSD.spa from the user input, simply put it all on curr1
    and it will be returned as is.
    """
    curr2     = ""
    sep       = "/"
    extension = ""

    if len(args) > 0:
        try:
            curr2 = args[0]
            if args[1] == '_':
                sep = ""
            else:
                sep = args[1]
            extension = args[2]
        except IndexError:
            pass

    symbol_name = curr1
    if curr2 != "":         #if a counter symbol is provided, use the separator and extensions
        symbol_name += sep + curr2 + extension
    return symbol_name

def parse_fix_options(user_input):
    split_options = user_input.split(' -')   #split by spaces
    action = split_options[0].strip()       #first item is the action to take

    options = {}
    for field in split_options[1:]:
        _field = field.strip().split()
        key          = _field[0]
        if len(_field[1:]) == 1:
            val      = _field[1]
        elif len(_field[1:])==0:
            print0("Value for tag {} not provided".format(key))
            raise IndexError
        else:
            val      = _field[1:]
            if isSymbolTag(key):
                val  = set_asset_name(val[0],*val[1:])
            else:
                print0("Error when parsing using input. Too many values for tag {}".format(key))
        options[key] = val

    return action, options
