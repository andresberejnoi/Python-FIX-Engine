import matplotlib.pyplot as plt
from mpl_finance import candlestick_ohlc
import matplotlib.dates as mdates
import matplotlib.animation as animation
from matplotlib import style
import pandas as pd
import re   #for regular expressions

class Plotter(object):
    def __init__(self,datastream,args):
        self.datastream = datastream
        self.args       = args
        #self._interval  = args.interval
        self.fig        = plt.figure()
        self.ax1        = self.fig.add_subplot(1,1,1)
        self.plot_func  = None
        self.plot_refresh_rate = args.plot_refresh_rate
        self._candle_width     = args.candle_width
        self._width            = self._convert_candleWidth_to_chartWidth()
        plt.xlabel('Timestamp')
        plt.ylabel('Price')

        self._set_plot_function()

    @property
    def candle_width(self):
        return self._candle_width
    def _convert_candleWidth_to_chartWidth(self):
        # determine the frequency of the bars
        num_freq  = re.findall('\d+', self.candle_width)[0]
        timeframe = re.findall('[a-z]+',self.candle_width,re.I)[0].lower()
        #print('TIMEFRAME:',timeframe)
        #Define default number of candles in a day if we assume each candle is 1 second thick
        hours = 24          #bars per day
        mins  = 60          #bars per hour
        secs  = 60          #bars per minute
        num_candles = hours * mins * secs

        #Modify number of candles based on requested bar width
        bar_reduction_rate = 0.85
        if timeframe == 's':
            bar_thickness   = int(num_freq) * bar_reduction_rate
        elif timeframe == 't' or timeframe == 'min':
            bar_thickness   = (int(num_freq) * 60) * bar_reduction_rate
            #print('We are here. Bar_thickness:',bar_thickness)
        new_num_candles = num_candles / bar_thickness

        return 1./new_num_candles

    def clear_canvas(self):
        self.ax1.clear()
    def _set_plot_function(self):
        if self.args.plot_mode.lower() == 'tick':
            self.plot_func = self._tick_plotter
        elif self.args.plot_mode.lower() == 'candle':
            self.plot_func = self._candle_plotter
    def _tick_plotter(self,i):
        self.ax1.clear()
        for label in self.ax1.xaxis.get_ticklabels():
            label.set_rotation(45)
        self.ax1.plot(self.datastream.timestamps,self.datastream.bids)
    def _candle_plotter(self,i):
        '''Function to animate a live chart using matplotlib.animation.FuncAnimation.
        It is defined here for convenience but I will look for a more elegant solution later.'''

        ohlc_df = self.datastream.get_ohlc(self.candle_width)#['bid']
        ohlc_df.set_index('datetime',inplace=True)
        ohlc_df = ohlc_df['bid']
        ohlc_df.reset_index(inplace=True)

        ohlc_df['datetime'] = pd.to_datetime(ohlc_df['datetime'])
        ohlc_df['datetime'] = ohlc_df["datetime"].apply(mdates.date2num)
        self.ax1.clear()
        for label in self.ax1.xaxis.get_ticklabels():
            label.set_rotation(45)
        candlestick_ohlc(self.ax1, ohlc_df.values, width=self._width, colorup='green', colordown='red')
        self.ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))

    def plot(self):
        ani = animation.FuncAnimation(self.fig, self.plot_func, interval=self.plot_refresh_rate)      #fig is the canvas we are drawing on. animate is the animation function we defined above. interval is the frecuency (in milliseconds) of refresh for the canvas
        plt.show()
