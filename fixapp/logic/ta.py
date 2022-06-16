"""
The following script has been adapted from the one here: https://www.quantopian.com/posts/technical-analysis-indicators-without-talib-code
It did not work with current version of Pandas, so I had to modify the functions
"""
import numpy
import pandas as pd
import math as m
import sys

def __list_indicators():
    thismodule = sys.modules[__name__]
    names = dir(thismodule)
    filtered_names = []
    for n in names:
        if n.startswith('__') or n == 'get_indicator':
            continue
        else:
            if __is_callable(n):
                filtered_names.append(n)

    return filtered_names

def __is_callable(name):
    thismodule = sys.modules[__name__]
    if callable(getattr(thismodule,name,None)):
        return True
    else:
        return False

def get_indicator(name):
    thismodule = sys.modules[__name__]
    allowed_names = {n.lower():n for n in __list_indicators()}
    n = name.lower()
    try:
        func_name = allowed_names[n]
        func      = getattr(thismodule,func_name,None)      #this will return None if func_name is not found in module
    except KeyError:
        return None

    return func
    '''
    if name.lower() in allowed_names:
        print("NAME IS IN ALlowED NAMES!")
        func_name = allowed_names[name.lower()]
        func = getattr(thismodule,func_name,None)    #if attribute is not found return None
        return func
    else:
        return None
    '''

class ExpertAdvisor(object):
    def __init__(self):
        self.indicator = None
    def analysize(self,data,*args):
        result = self.indicator(data,*args)


#===============================================================================
#Currently, these functions are returning the entire dataframe plus the new column, and maybe what I need is to simply return the new data column

#Moving Average
def MA(df, n):
    MA = pd.Series(df['close'].rolling(window=n,center=False).mean(), name='MA_' + str(n))
    #df = df.join(MA)
    return MA

#Exponential Moving Average
def EMA(df, n):
    #EMA = pd.Series(pd.ewma(df['close'], span = n, min_periods = n - 1), name = 'EMA_' + str(n))
    EMA = pd.Series(df['close'].ewm(span=n,min_periods = n - 1).mean(),name='EMA_' + str(n))
    #df = df.join(EMA)
    return EMA

#Momentum
def MOM(df, n):
    M = pd.Series(df['close'].diff(n), name = 'Momentum_' + str(n))
    #df = df.join(M)
    return M

#Rate of Change
def ROC(df, n):
    M = df['close'].diff(n - 1)
    N = df['close'].shift(n - 1)
    ROC = pd.Series(M / N, name = 'ROC_' + str(n))
    #df = df.join(ROC)
    return ROC

#Average True Range
def ATR(df, n):
    i = 0
    TR_l = [0]
    while i < df.index[-1]:
        TR = max(df.get_value(i + 1, 'high'), df.get_value(i, 'close')) - min(df.get_value(i + 1, 'low'), df.get_value(i, 'close'))
        TR_l.append(TR)
        i = i + 1
    TR_s = pd.Series(TR_l)
    ATR = pd.Series(TR_s.ewm(span=n,min_periods=n-1).mean(),name='ATR_' + str(n))
    #ATR = pd.Series(pd.ewma(TR_s, span = n, min_periods = n), name = 'ATR_' + str(n))
    #df = df.join(ATR)
    return ATR

#Bollinger Bands
def BBANDS(df, n):
    #MA = pd.Series(pd.rolling_mean(df['close'], n))
    MA = pd.Series(df['close'].rolling(window=n).mean())
    #MSD = pd.Series(pd.rolling_std(df['close'], n))
    MSD = pd.Series(df['close'].rolling(window=n).mean())
    b1 = 4 * MSD / MA
    B1 = pd.Series(b1, name = 'BollingerB_' + str(n))
    df = df.join(B1)
    b2 = (df['close'] - MA + 2 * MSD) / (4 * MSD)
    B2 = pd.Series(b2, name = 'Bollinger%b_' + str(n))
    df = df.join(B2)
    return df

#Pivot Points, Supports and Resistances
def PPSR(df):
    PP = pd.Series((df['high'] + df['low'] + df['close']) / 3)
    R1 = pd.Series(2 * PP - df['low'])
    S1 = pd.Series(2 * PP - df['high'])
    R2 = pd.Series(PP + df['high'] - df['low'])
    S2 = pd.Series(PP - df['high'] + df['low'])
    R3 = pd.Series(df['high'] + 2 * (PP - df['low']))
    S3 = pd.Series(df['low'] - 2 * (df['high'] - PP))
    psr = {'PP':PP, 'R1':R1, 'S1':S1, 'R2':R2, 'S2':S2, 'R3':R3, 'S3':S3}
    PSR = pd.DataFrame(psr)
    df = df.join(PSR)
    return df

#Stochastic oscillator %K
def STOK(df):
    SOk = pd.Series((df['close'] - df['low']) / (df['high'] - df['low']), name = 'SO%k')
    #df = df.join(SOk)
    return SOk

# Stochastic Oscillator, EMA smoothing, nS = slowing (1 if no slowing)
def STO(df,  nK, nD, nS=1):
    SOk = pd.Series((df['close'] - df['low'].rolling(nK).min()) / (df['high'].rolling(nK).max() - df['low'].rolling(nK).min()), name = 'SO%k'+str(nK))
    SOd = pd.Series(SOk.ewm(ignore_na=False, span=nD, min_periods=nD-1, adjust=True).mean(), name = 'SO%d'+str(nD))
    SOk = SOk.ewm(ignore_na=False, span=nS, min_periods=nS-1, adjust=True).mean()
    SOd = SOd.ewm(ignore_na=False, span=nS, min_periods=nS-1, adjust=True).mean()
    df = df.join(SOk)
    df = df.join(SOd)
    return df
# Stochastic Oscillator, SMA smoothing, nS = slowing (1 if no slowing)
def STO(df, nK, nD,  nS=1):
    SOk = pd.Series((df['close'] - df['low'].rolling(nKLow).min()) / (df['high'].rolling(nK).max() - df['low'].rolling(nK).min()), name = 'SO%k'+str(nK))
    SOd = pd.Series(SOk.rolling(window=nD, center=False).mean(), name = 'SO%d'+str(nD))
    SOk = SOk.rolling(window=nS, center=False).mean()
    SOd = SOd.rolling(window=nS, center=False).mean()
    df = df.join(SOk)
    df = df.join(SOd)
    return df
#Trix
def TRIX(df, n):
    #EX1 = pd.ewma(df['close'], span = n, min_periods = n - 1)
    EX1 = df['close'].ewm(span=n,min_periods=n-1).mean()
    #EX2 = pd.ewma(EX1, span = n, min_periods = n - 1)
    EX2 = EX1.ewm(span=n,min_periods=n-1).mean()
    #EX3 = pd.ewma(EX2, span = n, min_periods = n - 1)
    EX3 = EX2.ewm(span=2,min_periods=n-1).mean()
    i = 0
    ROC_l = [0]
    while i + 1 <= df.index[-1]:
        ROC = (EX3[i + 1] - EX3[i]) / EX3[i]
        ROC_l.append(ROC)
        i = i + 1
    Trix = pd.Series(ROC_l, name = 'Trix_' + str(n))
    df = df.join(Trix)
    return df

#Average Directional Movement Index
def ADX(df, n, n_ADX):
    i = 0
    UpI = []
    DoI = []
    while i + 1 <= df.index[-1]:
        UpMove = df.get_value(i + 1, 'high') - df.get_value(i, 'high')
        DoMove = df.get_value(i, 'low') - df.get_value(i + 1, 'low')
        if UpMove > DoMove and UpMove > 0:
            UpD = UpMove
        else: UpD = 0
        UpI.append(UpD)
        if DoMove > UpMove and DoMove > 0:
            DoD = DoMove
        else: DoD = 0
        DoI.append(DoD)
        i = i + 1
    i = 0
    TR_l = [0]
    while i < df.index[-1]:
        TR = max(df.get_value(i + 1, 'high'), df.get_value(i, 'close')) - min(df.get_value(i + 1, 'low'), df.get_value(i, 'close'))
        TR_l.append(TR)
        i = i + 1
    TR_s = pd.Series(TR_l)
    #ATR = pd.Series(pd.ewma(TR_s, span = n, min_periods = n))
    ATR = pd.Series(TR_s.ewm(span=n,min_periods=n).mean())
    UpI = pd.Series(UpI)
    DoI = pd.Series(DoI)
    #PosDI = pd.Series(pd.ewma(UpI, span = n, min_periods = n - 1) / ATR)
    PosDI = pd.Series(UpI.ewm(span=n,min_periods=n-1).mean() / ATR)
    #NegDI = pd.Series(pd.ewma(DoI, span = n, min_periods = n - 1) / ATR)
    NegDI = pd.Series(DoI.ewm(span=n,min_periods=n-1).mean() / ATR)
    #ADX = pd.Series(pd.ewma(abs(PosDI - NegDI) / (PosDI + NegDI), span = n_ADX, min_periods = n_ADX - 1), name = 'ADX_' + str(n) + '_' + str(n_ADX))
    ADX = pd.Series((abs(PosDI-NegDI) / (PosDI + NegDI)).ewm(span=n_ADX,min_periods=n_ADX - 1).mean(), name = 'ADX_' + str(n) + '_' + str(n_ADX))
    df = df.join(ADX)
    return df

#MACD, MACD Signal and MACD difference
def MACD(df, n_fast,n_slow):
    #EMAfast = pd.Series(pd.ewma(df['close'], span = n_fast, min_periods = n_slow - 1))
    EMAfast = pd.Series(df['close'].ewm(span=n_fast,min_periods=n_fast - 1).mean())
    #EMAslow = pd.Series(pd.ewma(df['close'], span = n_slow, min_periods = n_slow - 1))
    EMAslow = pd.Series(df['close'].ewm(span=n_slow,min_periods=n_slow -1).mean())
    MACD = pd.Series(EMAfast - EMAslow, name = 'MACD_' + str(n_fast) + '_' + str(n_slow))
    #MACDsign = pd.Series(pd.ewma(MACD, span = 9, min_periods = 8), name = 'MACDsign_' + str(n_fast) + '_' + str(n_slow))
    MACDsign = pd.Series(MACD.ewm(span=9,min_periods=8).mean(),name='MACDsign_' + str(n_fast) + '_' + str(n_slow))
    MACDdiff = pd.Series(MACD - MACDsign, name = 'MACDdiff_' + str(n_fast) + '_' + str(n_slow))
    df = df.join(MACD)
    df = df.join(MACDsign)
    df = df.join(MACDdiff)
    return df

#Mass Index
def MassI(df):
    Range = df['high'] - df['low']
    #EX1 = pd.ewma(Range, span = 9, min_periods = 8)
    EX1 = Range.ewm(span=9,min_periods=8).mean()
    #EX2 = pd.ewma(EX1, span = 9, min_periods = 8)
    EX2 = EX1.ewm(span=9,min_periods=8).mean()
    Mass = EX1 / EX2
    #MassI = pd.Series(pd.rolling_sum(Mass, 25), name = 'Mass Index')
    MassI = pd.Series(Mass.rolling(window=25).sum(), name = 'Mass Index')
    df = df.join(MassI)
    return df

#Vortex Indicator: http://www.vortexindicator.com/VFX_VORTEX.PDF
def Vortex(df, n):
    i = 0
    TR = [0]
    while i < df.index[-1]:
        Range = max(df.get_value(i + 1, 'high'), df.get_value(i, 'close')) - min(df.get_value(i + 1, 'low'), df.get_value(i, 'close'))
        TR.append(Range)
        i = i + 1
    i = 0
    VM = [0]
    while i < df.index[-1]:
        Range = abs(df.get_value(i + 1, 'high') - df.get_value(i, 'low')) - abs(df.get_value(i + 1, 'low') - df.get_value(i, 'high'))
        VM.append(Range)
        i = i + 1
    #VI = pd.Series(pd.rolling_sum(pd.Series(VM), n) / pd.rolling_sum(pd.Series(TR), n), name = 'Vortex_' + str(n))
    VI = pd.Series(pd.Series(VM).rolling(window=n).sum / pd.Series(TR).rolling(window=n).sum(), name = 'Vortex_' + str(n))
    df = df.join(VI)
    return df





#KST Oscillator
def KST(df, r1, r2, r3, r4, n1, n2, n3, n4):
    M = df['close'].diff(r1 - 1)
    N = df['close'].shift(r1 - 1)
    ROC1 = M / N
    M = df['close'].diff(r2 - 1)
    N = df['close'].shift(r2 - 1)
    ROC2 = M / N
    M = df['close'].diff(r3 - 1)
    N = df['close'].shift(r3 - 1)
    ROC3 = M / N
    M = df['close'].diff(r4 - 1)
    N = df['close'].shift(r4 - 1)
    ROC4 = M / N
    #KST = pd.Series(pd.rolling_sum(ROC1, n1) + pd.rolling_sum(ROC2, n2) * 2 + pd.rolling_sum(ROC3, n3) * 3 + pd.rolling_sum(ROC4, n4) * 4, name = 'KST_' + str(r1) + '_' + str(r2) + '_' + str(r3) + '_' + str(r4) + '_' + str(n1) + '_' + str(n2) + '_' + str(n3) + '_' + str(n4))
    KST = pd.Series(ROC1.rolling(window=n1).sum() + ROC2.rolling(window=n2).sum() * 2 + ROC3.rolling(window=n3).sum() * 3 + ROC4.rolling(window=n4).sum() * 4, name = 'KST_' + str(r1) + '_' + str(r2) + '_' + str(r3) + '_' + str(r4) + '_' + str(n1) + '_' + str(n2) + '_' + str(n3) + '_' + str(n4))
    df = df.join(KST)
    return df

#Relative Strength Index
def RSI(df, n):
    i = 0
    UpI = [0]
    DoI = [0]
    while i + 1 <= df.index[-1]:
        UpMove = df['High'].iat[i + 1] - df['High'].iat[i]
        DoMove = df['Low'].iat[i] - df['Low'].iat[i + 1]
        if UpMove > DoMove and UpMove > 0:
            UpD = UpMove
        else: UpD = 0
        UpI.append(UpD)
        if DoMove > UpMove and DoMove > 0:
            DoD = DoMove
        else: DoD = 0
        DoI.append(DoD)
        i = i + 1
    UpI = pd.Series(UpI)
    DoI = pd.Series(DoI)
    PosDI = pd.Series(UpI.ewm(span=n,min_periods = n -1).mean())
    NegDI = pd.Series(DoI.ewm(span = n, min_periods = n -1).mean())
    RSI = pd.Series(PosDI / (PosDI + NegDI))
    return RSI

#True Strength Index
def TSI(df, r, s):
    M = pd.Series(df['close'].diff(1))
    aM = abs(M)
    #EMA1 = pd.Series(pd.ewma(M, span = r, min_periods = r - 1))
    EMA1 = pd.Series(M.ewm(span=r,min_periods=r-1).mean())
    #aEMA1 = pd.Series(pd.ewma(aM, span = r, min_periods = r - 1))
    aEMA1 = pd.Series(aM.ewm(span=r, min_periods = r - 1).mean())
    #EMA2 = pd.Series(pd.ewma(EMA1, span = s, min_periods = s - 1))
    EMA2 = pd.Series(EMA1.ewm(span = s, min_periods = s - 1).mean())
    #aEMA2 = pd.Series(pd.ewma(aEMA1, span = s, min_periods = s - 1))
    aEMA2 = pd.Series(aEMA1.ewm(span = s, min_periods = s - 1).mean())
    TSI = pd.Series(EMA2 / aEMA2, name = 'TSI_' + str(r) + '_' + str(s))
    df = df.join(TSI)
    return df

#Accumulation/Distribution
def ACCDIST(df, n):
    ad = (2 * df['close'] - df['high'] - df['low']) / (df['high'] - df['low']) * df['volume']
    M = ad.diff(n - 1)
    N = ad.shift(n - 1)
    ROC = M / N
    AD = pd.Series(ROC, name = 'Acc/Dist_ROC_' + str(n))
    df = df.join(AD)
    return df

#Chaikin Oscillator
def Chaikin(df):
    ad = (2 * df['close'] - df['high'] - df['low']) / (df['high'] - df['low']) * df['volume']
    #Chaikin = pd.Series(pd.ewma(ad, span = 3, min_periods = 2) - pd.ewma(ad, span = 10, min_periods = 9), name = 'Chaikin')
    Chaikin = pd.Series(ad.ewm(span = 3, min_periods = 2).mean() - ad.ewm(span = 10, min_periods = 9).mean(), name = 'Chaikin')
    df = df.join(Chaikin)
    return df

#Money Flow Index and Ratio
def MFI(df, n):
    PP = (df['high'] + df['low'] + df['close']) / 3
    i = 0
    PosMF = [0]
    while i < df.index[-1]:
        if PP[i + 1] > PP[i]:
            PosMF.append(PP[i + 1] * df.get_value(i + 1, 'volume'))
        else:
            PosMF.append(0)
        i = i + 1
    PosMF = pd.Series(PosMF)
    TotMF = PP * df['volume']
    MFR = pd.Series(PosMF / TotMF)
    #MFI = pd.Series(pd.rolling_mean(MFR, n), name = 'MFI_' + str(n))
    MFI = pd.Series(MFR.rolling(window=n).mean(), name = 'MFI_' + str(n))
    df = df.join(MFI)
    return df

#On-balance volume
def OBV(df, n):
    i = 0
    OBV = [0]
    while i < df.index[-1]:
        if df.get_value(i + 1, 'close') - df.get_value(i, 'close') > 0:
            OBV.append(df.get_value(i + 1, 'volume'))
        if df.get_value(i + 1, 'close') - df.get_value(i, 'close') == 0:
            OBV.append(0)
        if df.get_value(i + 1, 'close') - df.get_value(i, 'close') < 0:
            OBV.append(-df.get_value(i + 1, 'volume'))
        i = i + 1
    OBV = pd.Series(OBV)
    #OBV_ma = pd.Series(pd.rolling_mean(OBV, n), name = 'OBV_' + str(n))
    OBV_ma = pd.Series(OBV.rolling(window=n).mean(), name = 'OBV_' + str(n))
    df = df.join(OBV_ma)
    return df

#Force Index
def FORCE(df, n):
    F = pd.Series(df['close'].diff(n) * df['volume'].diff(n), name = 'Force_' + str(n))
    df = df.join(F)
    return df

#Ease of Movement
def EOM(df, n):
    EoM = (df['high'].diff(1) + df['low'].diff(1)) * (df['high'] - df['low']) / (2 * df['volume'])
    #Eom_ma = pd.Series(pd.rolling_mean(EoM, n), name = 'EoM_' + str(n))
    Eom_ma = pd.Series(EoM.rolling(window=n).mean(), name = 'EoM_' + str(n))
    df = df.join(Eom_ma)
    return df

#Commodity Channel Index
def CCI(df, n):
    PP = (df['high'] + df['low'] + df['close']) / 3
    #CCI = pd.Series((PP - pd.rolling_mean(PP, n)) / pd.rolling_std(PP, n), name = 'CCI_' + str(n))
    CCI = pd.Series(PP - PP.rolling(window=n).mean() / PP.rolling(window=n).std(), name = 'CCI_' + str(n))
    df = df.join(CCI)
    return df

#Coppock Curve
def COPP(df, n):
    M = df['close'].diff(int(n * 11 / 10) - 1)
    N = df['close'].shift(int(n * 11 / 10) - 1)
    ROC1 = M / N
    M = df['close'].diff(int(n * 14 / 10) - 1)
    N = df['close'].shift(int(n * 14 / 10) - 1)
    ROC2 = M / N
    #Copp = pd.Series(pd.ewma(ROC1 + ROC2, span = n, min_periods = n), name = 'Copp_' + str(n))
    Copp = pd.Series((ROC1+ROC2).ewm(span = n, min_periods = n).mean(), name = 'Copp_' + str(n))
    df = df.join(Copp)
    return df

#Keltner Channel
def KELCH(df, n):
    #KelChM = pd.Series(pd.rolling_mean((df['high'] + df['low'] + df['close']) / 3, n), name = 'KelChM_' + str(n))
    KelChM = pd.Series(((df['high'] + df['low'] + df['close'])/3).rolling(window=n).mean(), name = 'KelChM_' + str(n))
    #KelChU = pd.Series(pd.rolling_mean((4 * df['high'] - 2 * df['low'] + df['close']) / 3, n), name = 'KelChU_' + str(n))
    KelChU = pd.Series(((4 * df['high'] - 2 * df['low'] + df['close']) / 3).rolling(window=n).mean(), name = 'KelChU_' + str(n))
    #KelChD = pd.Series(pd.rolling_mean((-2 * df['high'] + 4 * df['low'] + df['close']) / 3, n), name = 'KelChD_' + str(n))
    KelChD = pd.Series(((-2 * df['high'] + 4 * df['low'] + df['close']) / 3).rolling(window=n).mean(), name = 'KelChD_' + str(n))
    df = df.join(KelChM)
    df = df.join(KelChU)
    df = df.join(KelChD)
    return df

#Ultimate Oscillator
def ULTOSC(df):
    i = 0
    TR_l = [0]
    BP_l = [0]
    while i < df.index[-1]:
        TR = max(df.get_value(i + 1, 'high'), df.get_value(i, 'close')) - min(df.get_value(i + 1, 'low'), df.get_value(i, 'close'))
        TR_l.append(TR)
        BP = df.get_value(i + 1, 'close') - min(df.get_value(i + 1, 'low'), df.get_value(i, 'close'))
        BP_l.append(BP)
        i = i + 1
    #UltO = pd.Series((4 * pd.rolling_sum(pd.Series(BP_l), 7) / pd.rolling_sum(pd.Series(TR_l), 7)) + (2 * pd.rolling_sum(pd.Series(BP_l), 14) / pd.rolling_sum(pd.Series(TR_l), 14)) + (pd.rolling_sum(pd.Series(BP_l), 28) / pd.rolling_sum(pd.Series(TR_l), 28)), name = 'Ultimate_Osc')
    UltO = pd.Series((4 * pd.Series(BP_l).rolling(window=7).sum() / pd.Series(TR_l).rolling(window=7).sum()) + (2 * pd.Series(BP_l).rolling(window=14).sum() / pd.Series(TR_l).rolling(window=14).sum()) + (pd.Series(BP_l).rolling(window=28).sum() / pd.Series(TR_l).rolling(window=28).sum()), name = 'Ultimate_Osc')
    df = df.join(UltO)
    return df

#Donchian Channel
def DONCH(df, n):
    i = 0
    DC_l = []
    while i < n - 1:
        DC_l.append(0)
        i = i + 1
    i = 0
    while i + n - 1 < df.index[-1]:
        DC = max(df['high'].ix[i:i + n - 1]) - min(df['low'].ix[i:i + n - 1])
        DC_l.append(DC)
        i = i + 1
    DonCh = pd.Series(DC_l, name = 'Donchian_' + str(n))
    DonCh = DonCh.shift(n - 1)
    df = df.join(DonCh)
    return df

#Standard Deviation
def STDDEV(df, n):
    STD = pd.Series(df['close'].rolling(window=n).std(), name = 'STD_' + str(n))
    df = df.join(STD)
    #df = df.join(pd.Series(pd.rolling_std(df['close'], n), name = 'STD_' + str(n)))
    return df
