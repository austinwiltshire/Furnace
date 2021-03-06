""" Creates the asset abstraction which gives an OO interface to price data. Care must be taken to ensure this is
    efficient in non OO / relational contexts, and that it gives relational metaphors when those make sense. Indeed,
    an asset might be better looked at as a table, rather than a pure OO abstraction. It represents all price data,
    not just one day's worth """

from furnace.data import fcalendar
import numpy
import functools

def growth(begin, end):
    """ Calculates the percent growth between two values """
    return (end - begin) / begin

def annualized(unannualized_growth, days_represented):
    """ Returns the annualized growth or CAGR of growth if growth takes place over
    days represented """
    return pow(1.0 + unannualized_growth, 1.0 / (days_represented / fcalendar.trading_days_in_year())) - 1.0

def adjust_period(rate, original_period, new_period):
    """ Adjusts the rate given in to be the same rate over the new period. For example, adjusting
    annualized rates to daily rates would be adjust_period(rate, 252, 1). Rates are in % from 0 and
    periods are in trading days """

    daily_rate = pow(1.0 + rate, 1.0 / original_period) - 1.0
    return pow(daily_rate + 1.0, new_period) - 1.0

#TODO: what does this class actually offer over a dictionary?
class Universe(object):
    """ Represents a subset of tradable assets narrowed down for any particular strategy """
    def __init__(self, assets, factory):
        self._assets = dict((asset.symbol(), asset) for asset in assets)
        self._factory = factory

    def __getitem__(self, symbol):
        """ Grabs one of our assets based on the symbol """
        assert self.supports_symbol(symbol)
        return self._assets[symbol]

    def cardinality(self):
        """ Returns the size of this asset universe """
        return len(self._assets)

    #TODO: should our asset factory pass us the calendar directly and we query it rather than 
    #supporting this pass through function?
    #TODO: should we have some sort of idea of a combined factory-calendar or universe-calendar that
    #performs these queries rather than expecting just a plain factory/universe to do it?
    def supports_symbol(self, symbol):
        """ Returns true if this symbol is in the tradable universe """
        return symbol in self._assets.keys()

    def supports_date(self, date):
        """ Returns true if the underlying factory supports the date """
        return self._factory.supports_date(date)


    def __iter__(self):
        """ Iterates through all assets """
        return self._assets.itervalues()

#NOTE: data_cache is expected to be eager loaded (current design, anyway)
class Factory(object):
    """ Represents all tradable assets loaded """
    def __init__(self, data_cache, calendar):
        self._data_cache = data_cache
        self._calendar = calendar

    def make_asset(self, symbol):
        """ Creates an asset based on the ticker symbol """
        assert symbol in self._data_cache.keys()
        return Asset(symbol, self._data_cache[symbol], self._calendar)

    def supports_date(self, date_):
        """ Predicate on whether this asset universe can support the date passed in """
        return date_ in self._calendar

    def make_universe(self, symbols):
        """ Returns a universe of tradable assets restricted to those passed in """
        return Universe((self.make_asset(symbol) for symbol in symbols), self)

@functools.total_ordering
class Asset(object):
    """ Represents a tradable security, by symbol, over a period of time """
    def __init__(self, symbol, table, calendar):
        self._symbol = symbol
        self._table = table
        self._calendar = calendar

    #NOTE: this function is slow, especially in rapidly readjusted strategies, and has gone through two rounds of
    #optimization
    def make_index(self, begin_date, basis, end_date):
        """ Creates an index for this asset weighted initially at basis """
        table = self._table[(self._table.index >= begin_date) & (self._table.index <= end_date)][["Adjusted Close"]]
        table.columns = [self.symbol() + "_AdjustedPrice"]

        initial_basis = basis / table.ix[begin_date]
        table[self.symbol() + "_Basis"] = initial_basis[0]

        table[self.symbol() + "_Index"] = table[self.symbol() + "_AdjustedPrice"] * table[self.symbol() + "_Basis"]
        return table 

    #TODO add to some sort of helper class rather than reimplementing everywhere
    #TODO test
    def total_return(self, begin_date, end_date):
        """ The total return of this asset if held from the first date to the last date """
        table = self._table["Adjusted Close"]
        assert begin_date >= table.index[0]
        assert end_date <= table.index[-1]

        begin = self._table["Adjusted Close"].ix[begin_date]
        end = self._table["Adjusted Close"].ix[end_date]
        return growth(begin, end)

    def begin(self):
        """ Returns the first date that this asset table supports """
        return self._table.index[0]

    def end(self):
        """ Returns the last date that this asset table supports """
        return self._table.index[-1]

    #TODO: hand test this for spy
    def cagr(self, begin_date, end_date):
        """ The compound adjusted geometric return of this asset if held from the first date to the last date """
        table = self._table["Adjusted Close"]
        assert begin_date >= table.index[0]
        assert end_date <= table.index[-1]

        #NOTE: we add one to represent holding it both on the first and last days.
        return annualized(
                self.total_return(begin_date, end_date),
                self._calendar.number_trading_days_between(begin_date, end_date) + 1
                )

    #TODO: hand test this for spy
    #TODO: could potentially precalculate a rolling volatility all at once per asset and trading period
    def volatility(self, begin, end):
        """ The volatility of this asset over the entire data period """
        table = self._table["Adjusted Close"]
        assert begin >= table.index[0]
        assert end <= table.index[-1]

        table = table[table.index >= begin]
        variance = table[table.index <= end].pct_change().dropna().var()

        return numpy.sqrt(fcalendar.trading_days_in_year()*variance)

    #TODO: reevaluate when comissions are in to see if this can be taken back out
    def symbol(self):
        """ Getter for this assets symbol """
        return self._symbol

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
        #same symbol but might support different dates in their table indecies hash table
        return hash(self._symbol)

    def __repr__(self):
        return "Asset {0}".format([self._symbol])

    #TODO: currently just compare symbol, need to ensure things came from the same factory
    #and support the same dates
    def __lt__(self, rhs):
        return self._symbol < rhs.symbol()



