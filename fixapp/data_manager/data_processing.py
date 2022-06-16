__all__ = ['isInterval_complete','ohlc_resample','create_ohlc_datapoint','read_csv','read_csv_pepperstone','my_strptime']
import pandas as pd
import datetime as dt
from mpl_finance import candlestick_ohlc
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
#from matplotlib.finance import candlestick_ohlc

def isInterval_complete(time1,time2,interval):
    if (time2-time1) > interval:
        return True
    return False

def create_datetime_object(date_time_str):
    '''For now I will just take into account the hour and seconds.
    This is made for data coming from Fortex in tag 52 in the format YYYYmmdd-HH:MM:SS:fff'''
    #intra_day_str = date_time_str.split('-')[-1]
    if type(date_time_str) == str:
        return datetime.datetime.strptime(date_time_str, "%Y%m%d-%H:%M:%S.%f")
    return date_time_str

def create_ohlc_datapoint(start_time,prices):
    timestamp = create_datetime_object(start_time)
    high   = max(prices)
    low    = min(prices)
    open_  = prices[0]
    close_ = prices[-1]

    return (timestamp,open_,high,low,close_)


def build_argparser():
    parser = argparse.ArgumentParser(description="Perform some data processing on trading data")
    parser.add_argument('-i','--interval',type=str,default='15Min',help="Interval of bars to use")
    parser.add_argument('-f','--filename',type=str,help="Specify a file or path depending on context with other command arguments provided")
    parser.add_argument('-p','--plot_candles', action='store_true')
    #parser.add_argument('-f','--filename',type=str)
    args = parser.parse_args()
    return args

def read_csv(filename,headers=[]):
    data = pd.read_csv(filename, names=headers)
    return data

def read_csv_pepperstone(filename):
    interval = args.interval
    headers = ['symbol','date_time','bid','ask']
    data = read_csv(filename, headers=headers)
    #data['date_time'] = data['date_time'].apply(lambda x: my_strptime(x, '%d/%m/%Y %H:%M:%S.%f'))
    data['date_time'] = data['date_time'].apply(lambda x: dt.datetime.strptime(x, '%d/%m/%Y %H:%M:%S.%f'))
    bid_ohlc = data['bid'].resample(interval).ohlc()
    ask_ohlc = data['ask'].resample(interval).ohlc()
    data_bid_ask = pd.concat([bid_ohlc, ask_ohlc], axis=1, keys=['ask', 'bid'])

    return data_bid_ask
    # This has datetime as second column

def ohlc_resample(dataframe, interval):
    i = interval    #do some processing here to make the interval appropriate or to check for correct format
    headers = ['datetime','bid','ask']

    dataframe = dataframe.set_index('datetime')
    #bid_ask_ohlc['datetime'] = pd.to_datetime(bid_ask_ohlc['datetime'])
    dataframe.index = pd.to_datetime(dataframe.index, unit='s')

    bid_ohlc = dataframe['bid'].resample(i).ohlc()
    ask_ohlc = dataframe['ask'].resample(i).ohlc()
    data_bid_ask = pd.concat([bid_ohlc, ask_ohlc], axis=1, keys=['bid','ask'])
    data_bid_ask = data_bid_ask.reset_index()
    return data_bid_ask

def my_strptime(val, str_format):
    '''Function taken from https://ckyeungac.com/trading/493/python-processing-tick-data-into-one-minute-ohlc-with-a-4x-faster-strptime-function-and-pandas/
    because it is supposed to be faster than the built-in function datetime.datetime.strptime'''
    l = len(val)
    if str_format == '%d/%m/%Y %H:%M:%S.%f' and (l==23 or l==26):
        us = int(val[20:26])
        if l == 23:
            us *= 1000
        return dt.datetime(
            int(val[6:10]),
            int(val[3:5]),
            int(val[0:2]),
            int(val[11:13]),
            int(val[14:16]),
            int(val[17:19]),
            us)

def plot_candlestick_data(filename):
    if isinstance(filename, pd.DataFrame):
        new_data   = filename
        output_name = "dataframe_candles"
    else:
        new_data = pd.read_csv(filename)
        output_name = filename.split('.')[0]

    try:
        new_data = new_data.drop(columns='symbol')
    except KeyError:
        pass

    '''
    #------Prepare data by removing unnecessary columns
    new_data = pd.DataFrame({'datetime':pd.to_datetime(data['datetime']),
                             'open':data['open'],
                             'high':data['high'],
                             'low':data['low'],
                             'close':data['close']})

    new_data['datetime'] = new_data["datetime"].apply(mdates.date2num)
    '''
    new_data['datetime'] = pd.to_datetime(new_data['datetime'])
    new_data['datetime'] = new_data["datetime"].apply(mdates.date2num)

    f1, ax = plt.subplots(figsize = (10,5))
    # plot the candlesticks
    print(new_data.values)
    candlestick_ohlc(ax, new_data.values, width=1./(24*60*60), colorup='green', colordown='red')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
    # Saving image

    for label in ax.xaxis.get_ticklabels():
        label.set_rotation(45)
    plt.xlabel('Date')
    plt.ylabel('Price')
    #plt.show()
    plt.show()

    print('-'*20)
    save_img_flag = input("Save image to {}? (y/n): ".format(output_name))

    if save_img_flag == 'y' or save_img_flag == 'yes':
        f1.savefig('{}.png'.format(output_name))
    else:
        print("\nImage not saved")

    print('-'*20)



def main(args):
    if args.plot_candles:
        filename = args.filename
        plot_candlestick_data(filename)
    else:
        source_data = args.filename
        data = read_csv_pepperstone(source_data)
        print(data.shape)
        print(data)

if __name__ == '__main__':
    import argparse
    args = build_argparser()
    main(args)
