""" Creates the asset abstraction which gives an OO interface to price data. Care must be taken to ensure this is
    efficient in non OO / relational contexts, and that it gives relational metaphors when those make sense. Indeed,
    an asset might be better looked at as a table, rather than a pure OO abstraction. It represents all price data,
    not just one day's worth """

class AssetUniverse(object):
    """ Represents all tradable assets for any particular model. """
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

    def __iter__(self):
        return self._assets.itervalues()

    def restricted_to(self, supported_symbols):
        """ Subsets this asset universe on the passed in symbols """
        assert set(supported_symbols).issubset(self._supported_symbols)

        return AssetUniverse(supported_symbols, self._data_cache, self._calendar)

    def cardinality(self):
        """ Returns the size of this asset universe """
        return len(self._supported_symbols)


class Asset(object):
    """ Represents a tradable security, by symbol, over a period of time """
    def __init__(self, symbol, data_cache, calendar):
        self._symbol = symbol
        self._data_cache = data_cache
        self._calendar = calendar
        self._data_cache["Yield"] = self._data_cache['Dividends'] / self._data_cache['Close']
        accumulated_yield = (self._data_cache["Yield"] + 1.0).dropna().cumprod()

        #note: we assume dividends are reinvested on the day of
        self._data_cache["Basis Adjustment"] = accumulated_yield.reindex(self._data_cache.index,
                                                                         method='ffill',
                                                                         fill_value=1.0)
        self._data_cache["Adjusted Close"] = self._data_cache["Close"] * self._data_cache["Basis Adjustment"]

    def table(self):
        """ Accessor for the table this object is based on """
        return self._data_cache

    def symbol(self):
        """ Accessor for symbol this object is based on """
        return self._symbol

