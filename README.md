# FIX Client

**Use AUTO MODE**. Take a look at the text below in the auto mode section, which is the one working at the moment. I made changes and did not implement the manual version again. 

Additionally, take a look at the [blog post](https://andresberejnoi.com/implementing-fix-engine-python/) I wrote about this project.

## Setup
I will include the steps for the particular setup I am using to run the FIX client. To begin with, I am running a conda version of Python 3.7. Simply go to the miniconda [website](https://docs.conda.io/en/latest/miniconda.html) and download the Python 3.7 installer for the appropriate OS (I am using Ubuntu 18.04 LTS).

After downloading and installing, use conda to create a virtual environment so that nothing else interferes with the project's packages:

```sh
conda create -n auto_trader python=3.7
```
*auto_trader* is the name of the virtual environment and it can be anything. We also tell it to install Python in the virtual environment. Then activate the virtual environment:

```sh
conda activate auto_trader
```

Once inside the virtual environment, go to the project folder for this client and install all dependencies:

```sh
pip install -r requirements.txt
```

## How to Use (Manual Mode)

There are several command line arguments that can be passed to the script when running from the terminal. To see a list of all the ones included simply type:

```sh
python main.py --help
```

The resulting list will show all the options that the script listens to, although not all of them might be implemented.

An example run can be done with the following command:

```sh
python main.py --config <config_file_name>
```

The configuration file *config_file_name* should contain two sessions: one for trade and another one for quotes. If it has only one then the client will probably still work but if an action from a different session is requested then it might crash. I will eventually fix it so that it works again with single session files.

From the CLI one can perform actions such as selling, buying, or subscribing/unsubscribing to market data from the counterparty. An action must be followed by 'tags' from the FIX protocol. Each is tag preceeded with a hyphen '-' and followed by its corresponding value. For example:


```
1 -55 EUR/USD -44 1.145 -38 100000
```

The example above indicates a buy order (NewOrderSingle) for the symbol 'EUR/USD' (this is particular of Tier1FX) at a price of $1.145 and an order size of 100000.

The Symbol tag (-55) can receive arguments in a few ways:

```
... -55 EUR USD _ .spa ...
```

resulting in:

```py
"EURUSD.spa"
```

or
```
... -55 EUR USD / ...
```

resulting in:

```py
"EUR/USD"
```

or simply type it all together:

```
... -55 EUR/USD ...
```

### Example Run

I will list a concrete set of commands to run the program. The first step is to be inside the virtual environment and have all dependencies installed as indicated in the setup step above.

We can start the script by running the script from the terminal:

```sh
python main.py --config configs/fix/twoSess_tier1.cfg -i 5-Sec -vvv
```
**-config** tells the path to a configuration file to set up the fix application.

**-i** tells the interval we want for candlesticks to be saved at the end of the program. '5-Sec' means each candlestick will be 5 seconds wide.

Now we will get to the command line interface which will have a menu like:

```
FIX application has started...
Enter an action to perform:
*	1 -> Place Buy Order
*	2 -> Place Sell Order
*	3 -> Subscribe to Market Data
*	4 -> Cancel Market Data Subscription
*	5 -> Order Cancel Request
*	6 -> Order Status Request

*	logout -> Logout and Exit
*	d -> Start debugger

[Action]:
```

At the action prompt enter:
```
1 -55 EUR/USD
```
This will send a purchase order to the server and we will receive an execution report (35=8) with information about the trade.

After that, we can request market data to save in OHLC (Open, High, Low, Close) at the end of the program run. Again, at the action prompt enter:
```
3 -55 EUR/USD
```
The script will start printing the quote updates in a loop to the terminal. It will look something like this:
```
FROM APP:
8=FIX.4.4|9=185|35=W|34=4584|49=FIXUAT3-QUOTE.FORTEX.COM|52=20190417-16:36:35.842|56=T1DEMO_FIX_QS|55=EUR/USD|262=1-1555531084.394086|268=2|269=0|270=1.129820|271=500000|269=1|270=1.129830|271=1000000|10=044|
================================================================================
Market Data Snapshot/Full Refresh (35=W)
```
The program will also print to the terminal each time a new candlestick is created after collecting enough tick data. The print message will look like:
```
|===> OHLC datapoint added
|===> OHLC datapoint added
```
There are two data points created, one for the bid price and one for the ask price as they are treated separately.

A data subscripton can be canceled with:
```
4 -55 EUR/USD
```
Since the program is running and printing in a loop and I have not added a good way to keep the interface in place, while typing the command, it is likely that it will be dragged up with the text that is being printed. You can also simply **logout** from the session to quit all processes.

To logout, type the command at the action prompt:
```
logout
```
This will stop the fix app and will automatically save all the candlestick data generated during the run into a new folder ***data/*** under the root directory of the project.

The output filename will have a format of `bid_ohlc_<time_interval>_<file_count>.csv`. For our market data request above, the output file will be saved at:
```
data/bid_ohlc_5_Sec_1.csv
data/ask_ohlc_5_Sec_1.csv
```

---
## How to Use (Auto Mode)
I have included another script that performs trade actions automatically. It is a work in progress for now and more options will be added. Right now, the options that can be controlled from the command line are:
* Configuration file (-config)
* Verbose mode  (-v or --verbose)
* Plotting flag (-p or --plot)
* Plotting Mode (-pm or --plot_mode)
* Symbol        (-s or --symbol)

An example run with all the options activated would be:

```sh
python main.py --config configs/fix/twoSess_tier1.cfg -vv -p -pm candles -s EUR/USD
```
The verbose mode is set to level 2 (-vv) so that price quote updates gets printed to the console. `-p` and `-pm` flags will control the way plotting is done. Right now the chart is very primitive. If `-p` is included, then the program will plot the live data into a matplotlib figure. We can use `-pm` to decide to use raw tick data by passing the string `tick` or we can use compressed data by passing the string `candle`. 

The script will begin setting up the FIX sessions with the broker and will wait several seconds until there is any quote data coming in before it starts trading.

The example uses a simple `RSI` strategy to send a buy order when RSI<30, a sell order when RSI>70, or a hold order otherwise.

---
## Plotting Candles From File  

To check the output candlestick data, use the **data_processing.py** module in the following way:
```
python data_processing.py -p -f data/bid_ohlc_5_Sec_1.csv
```

This will display a **matplotlib** chart. After closing the figure, there will be an option for saving the figure by selecting **y** or **n**. The image will be saved with the same name as the input csv, but in **.png** format.

## Verbose Mode
I decided to implement a verbose mode to the program because all the print statements were cluttering the main execution but I could not simply remove them since sometimes they are useful.

A solution I found is to use the logging module and accept a **--verbose** or **-v** parameter at the command line. I defined four levels of verbosity based on how important the messages are for a normal run. They follow the convention:
- No **-v** flag:
  - Equivalent to quiet. Only some messages at setup and errors will get printed
- **-v** (level 1 verbosity)
  - Messages to indicate that an action was performed succcessfully or not, and normal print messages with useful info will get printed (along with anything from the lower verbosity levels)
- **-vv** (level 2 verbosity)
  - FIX messages coming from the server will get printed. It can be execution reports, reject messages, market data refresh updates, etc.
- **-vvv** (level 3 verbosity)
  - FIX messages sent from fromAdmin, toAdmin, or FIX messages in general sent with this client to the outside will be printed at this level.

Any verbosity level includes the level below, so **-vvv** will print everything that the program could possibly print.


## Requirements (in progress)
A better list of requirements might be in the requirements.txt file. To install them simply go to a terminal and follow the steps on how to setup above

The instructions should be all that is needed, but I included some information below in case quickfix needs to be installed manually.

- Python 3.x
- QuickFIX
  - You can get a wheel file from this [link](https://www.lfd.uci.edu/~gohlke/pythonlibs/#quickfix) and then install with pip
  - You can also build it from the source code from [here](https://github.com/quickfix/quickfix) (I had trouble doing this on Windows 10).
  - On Ubuntu 18.04 I had no trouble installing through pip like any other Python package.
  - On Fedora 36, I just needed to make sure that gcc-c++ was installed: `sudo dnf install gcc-c++`
- BeautifulSoup
- Matplotlib
- Pandas
- Backtrader? (not included yet)
