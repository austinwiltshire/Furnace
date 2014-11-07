""" Creates the asset abstraction which gives an OO interface to price data. Care must be taken to ensure this is
    efficient in non OO / relational contexts, and that it gives relational metaphors when those make sense. Indeed,
    an asset might be better looked at as a table, rather than a pure OO abstraction. It represents all price data,
    not just one day's worth """

from furnace.data import fcalendar
import numpy

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

        #note: we assume dividends are reinvested on the day of
        self._table["Basis Adjustment"] = accumulated_yield.reindex(self._table.index,
                                                                         method='ffill',
                                                                         fill_value=1.0)
        self._table["Adjusted Close"] = self._table["Close"] * self._table["Basis Adjustment"]

    #NOTE: this function is slow, especially in rapidly readjusted strategies
    #TODO: why not set an end to the index? a lot of the index values are thrown away for fast changing dates
    def make_index(self, date, basis):
        """ Creates an index for this asset weighted initially at basis """
        table = self._table[self._table.index >= date]

        initial_basis = basis / table.ix[date]['Adjusted Close']

        return table['Adjusted Close'] * initial_basis

#TODO: hand test this for spy
    #TODO 1.1 this should take in a begin/end period
    def cagr(self):
        """ The compound adjusted geometric return of this asset if held from the first date to the last date """
        begin = self._table["Adjusted Close"].ix[0]
        end = self._table["Adjusted Close"].ix[-1]
        total_return = (end - begin) / begin
        days_available = len(self._table)
        return pow(1.0 + total_return, 1.0 / (days_available / fcalendar.trading_days_in_year())) - 1.0

#TODO: hand test this for spy
    #TODO 1.1 this should take in a begin/end period
    def volatility(self):
        """ The volatility of this asset over the entire data period """
        
        return numpy.sqrt(fcalendar.trading_days_in_year()*self._table["Adjusted Close"].pct_change().dropna().var())

#TODO: hand test this for spy
    def simple_sharpe(self):
        """ Returns the simplified sharpe ratio of this asset over the entire data period """
        return self.cagr() / self.volatility()

    def yahoo_adjusted_return(self, begin, end):
        """ Helper method to get yahoo's own reported return, useful for debugging """
        first = self._table.ix[begin]['Adj Close']
        last = self._table.ix[end]['Adj Close']
        return (last - first) / first

#TODO: probably need to make sure these things came from the same factory
    def __eq__(self, other):
        return self._symbol == other #pylint: disable=W0212


