""" Creates the asset abstraction which gives an OO interface to price data. Care must be taken to ensure this is
    efficient in non OO / relational contexts, and that it gives relational metaphors when those make sense. Indeed,
    an asset might be better looked at as a table, rather than a pure OO abstraction. It represents all price data,
    not just one day's worth """

from furnace.data import fcalendar
import numpy

def growth(begin, end):
    """ Calculates the percent growth between two values """
    return (end - begin) / begin

def annualized(growth, days_represented):
    """ Returns the annualized growth or CAGR of growth if growth takes place over
    days represented """
    return pow(1.0 + growth, 1.0 / (days_represented / fcalendar.trading_days_in_year())) - 1.0

def adjust_period(rate, original_period, new_period):
    """ Adjusts the rate given in to be the same rate over the new period. For example, adjusting
    annualized rates to daily rates would be adjust_period(rate, 252, 1). Rates are in % from 0 and
    periods are in trading days """

    daily_rate = pow(1.0 + rate, 1.0 / original_period) - 1.0
    return pow(daily_rate + 1.0, new_period) - 1.0

#TODO: this is more of an asset factory. An asset universe is a separate set of assets and probably needs
#to be it's own object.
class AssetUniverse(object):
    """ Represents all tradable assets for any particular model. """
    #TODO: move self._assets line to a factory function
    def __init__(self, supported_symbols, data_cache, calendar):
        self._data_cache = data_cache
        self._calendar = calendar
        self._supported_symbols = set(supported_symbols)

        #NOTE: cached for great performance
        self._assets = dict((name, self.make_asset(name)) for name in self._supported_symbols)

    def make_asset(self, symbol):
        """ Creates an asset based on the ticker symbol """
        assert symbol in self._supported_symbols
        return Asset(symbol, self._data_cache[symbol], self._calendar)

    def supports_date(self, date_):
        """ Predicate on whether this asset universe can support the date passed in """
        return date_ in self._calendar

    def supports_symbol(self, symbol):
        """ Predicate on whether symbol is in this asset universe """
        return symbol in self._supported_symbols

    def cardinality(self):
        """ Returns the size of this asset universe """
        return len(self._supported_symbols)


class Asset(object):
    """ Represents a tradable security, by symbol, over a period of time """
    #TODO: add complex initialization to factory function
    def __init__(self, symbol, data_cache, calendar):


        self._symbol = symbol
        self._table = data_cache
        self._calendar = calendar
        self._table["Yield"] = self._table['Dividends'] / self._table['Close']
        accumulated_yield = (self._table["Yield"] + 1.0).dropna().cumprod()

        #pull all splits forward in time, and fill any remaining nulls with 1
        self._table["Split Adjustment"] = self._table["SplitRatio"].fillna(method='ffill').fillna(1)

        #note: we assume dividends are reinvested on the day of
        self._table["Basis Adjustment"] = accumulated_yield.reindex(self._table.index,
                                                                         method='ffill',
                                                                         fill_value=1.0)
        self._table["Adjusted Close"] = (self._table["Close"] *
                                         self._table["Basis Adjustment"] *
                                         self._table["Split Adjustment"])

    #NOTE: this function is slow, especially in rapidly readjusted strategies
    #TODO: why not set an end to the index? a lot of the index values are thrown away for fast changing dates
    def make_index(self, begin_date, basis, end_date):
        """ Creates an index for this asset weighted initially at basis """
        table = self._table[(self._table.index >= begin_date) & (self._table.index <= end_date)]["Adjusted Close"]

        initial_basis = basis / table.ix[begin_date]

        return table * initial_basis

    #TODO 1.1 add to some sort of helper class rather than reimplementing everywhere
    #TODO 1.1 test
    def total_return(self, begin_date, end_date):
        """ The total return of this asset if held from the first date to the last date """
        table = self._table["Adjusted Close"]
        assert begin_date >= table.index[0]
        assert end_date <= table.index[-1]

        begin = self._table["Adjusted Close"].ix[begin_date]
        end = self._table["Adjusted Close"].ix[end_date]
        return growth(begin, end)

    def begin(self):
        return self._table.index[0]

    def end(self):
        return self._table.index[-1]

#TODO: hand test this for spy
    #TODO 1.1 this should take in a begin/end period
    def cagr(self, begin_date, end_date):
        """ The compound adjusted geometric return of this asset if held from the first date to the last date """
        table = self._table["Adjusted Close"]
        assert begin_date >= table.index[0]
        assert end_date <= table.index[-1]

        #NOTE: we add one to represent holding it both on the first and last days.
        return annualized(
                self.total_return(begin_date, end_date),
                self._calendar.trading_days_between(begin_date, end_date) + 1
                )

#TODO: hand test this for spy
    #TODO 1.1 this should take in a begin/end period
    #TODO: could potentially precalculate a rolling volatility all at once per asset and trading period
    def volatility(self, begin, end):
        """ The volatility of this asset over the entire data period """
        table = self._table["Adjusted Close"]
        assert begin >= table.index[0]
        assert end <= table.index[-1]

        table = table[table.index >= begin]
        variance = table[table.index <= end].pct_change().dropna().var()

        return numpy.sqrt(fcalendar.trading_days_in_year()*variance)

#TODO: hand test this for spy
    def simple_sharpe(self, begin_date, end_date):
        """ Returns the simplified sharpe ratio of this asset over the entire data period """
        return self.cagr(begin_date, end_date) / self.volatility(begin_date, end_date)

    def yahoo_adjusted_return(self, begin, end):
        """ Helper method to get yahoo's own reported return, useful for debugging """
        first = self._table.ix[begin]['Adj Close']
        last = self._table.ix[end]['Adj Close']
        return (last - first) / first

#TODO: probably need to make sure these things came from the same factory
    def __eq__(self, other):
        return self._symbol == other #pylint: disable=W0212

    def __hash__(self):
        #TODO: currently this object conflates the abstract idea of an asset symbol as well as a set amount
        #of asset + date data. the hash only reflects the symbol itself, meaning that two assets with the
        #same symbol but one using different dates (using the 'between' helper) would conflict in the same
        #hash table
        return hash(self._symbol)

    def __repr__(self):
        return "Asset with Symbol: {1}".format([self._symbol])


