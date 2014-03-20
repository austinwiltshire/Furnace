""" Creates the asset abstraction which gives an OO interface to price data. Care must be taken to ensure this is
    efficient in non OO / relational contexts, and that it gives relational metaphors when those make sense. Indeed,
    an asset might be better looked at as a table, rather than a pure OO abstraction. It represents all price data,
    not just one day's worth """

import datetime
import operator
import numpy
from furnace.data import fcalendar

class AssetFactory(object):
    def __init__(self, data_cache):
        self._data_cache = data_cache

    def make_asset(self, symbol):
        """ Creates an asset based on the ticker symbol """
        return Asset(symbol, self._data_cache)

class Asset(object):
    """ Represents a tradable security, by symbol """
    def __init__(self, symbol, data_cache):
        self._symbol = symbol
        self._data_cache = data_cache

    def _dividends(self):
        """ List of all available dividends """
        return sorted([div for div in self._data_cache[self._symbol]["dividends"].itervalues()],
                      key=lambda d: d["Date"])

    def _price_dates_available(self):
        """ List of all dates available for this asset's price data """
        return self._data_cache[self._symbol]["price"].keys()

    def _first_price_date(self):
        """ Returns the first date available in the data cache for this asset """
        return min(self._price_dates_available())

    def _last_price_date(self):
        """ Returns the last date available in the data cache for this asset """
        return max(self._price_dates_available())

    def price(self, date):
        """ Returns the price of this asset given a date. Currently returns the closing price. """
        #TODO: use financial datetime library to elevate key errors on weekends and non trading dates

        assert date in fcalendar.ALL_TRADING_DAYS
        assert self._first_price_date() <= date <= self._last_price_date()

        return self._data_cache[self._symbol]["price"][date]["Close"]

    def _adj_price(self, date):
        """ A helper method to get yahoo's adjusted price out of the data. Useful for testing that dividend accural
            algorithms are accurate. """

        assert date in fcalendar.ALL_TRADING_DAYS
        assert self._first_price_date() <= date <= self._last_price_date()

        return self._data_cache[self._symbol]["price"][date]["Adjusted Close"]

    def average_yield(self):
        """ Returns the average dividend yield on a *per dividend* basis for this asset
            This is not annualized! """
        yields = [div["Dividend"] / self.price(div["Date"]) for div in self._dividends()]

        return numpy.average(yields)

    def average_dividend_period(self):
        """ Returns the average period between dividend dispersals for this asset """
        dates = [div["Date"] for div in self._dividends()]
        average_days_period = [(later - earlier).days for (earlier, later) in zip(dates[:-1], dates[1:])]
        return numpy.average(average_days_period)

    def yield_between(self, begin, end):
        """ Returns the dividend yield (raw dividends / share price at the time) between begin and end """
        assert begin <= end, "Beginning date should happen before or during end date"

        dividends_in_range = [div for div in self._dividends() if begin < div["Date"] <= end]
        yields = [div["Dividend"] / self.price(div["Date"]) for div in dividends_in_range]
        return reduce(operator.mul, [1.0 + yield_ for yield_ in yields], 1.0) - 1.0

    def _expected_daily_accrued_yield(self):
        """ Returns the expected daily, non compounded, yield of this asset """
        return self.average_yield() / self.average_dividend_period()

    def _estimate_yield_accrued(self, next_dividend, past_dividend, date):
        """ Estimates the yield accrued between dividends when one is not available """
        assert not (next_dividend and past_dividend)

        days_in = ((date - past_dividend["Date"]).days
                   if not next_dividend
                   else self.average_dividend_period() - (next_dividend["Date"] - date).days)

        if days_in > self.average_dividend_period() or days_in < 0.0:
            raise Exception("Too late or early to estimate dividends")

        return days_in * self._expected_daily_accrued_yield()

    def _calculate_yield_accrued(self, next_dividend, past_dividend, date):
        """ Calculates the portion of the dividend yield accrued on date assuming both dividends are valid """
        assert next_dividend and past_dividend

        days_between = float((next_dividend["Date"] - past_dividend["Date"]).days)
        yield_ = next_dividend["Dividend"] / self.price(date)
        days_in = float((date - past_dividend["Date"]).days)

        return days_in / days_between * yield_

    def yield_accrued(self, date):
        """ Returns the yield accrued to this asset at date.
            Accrued means the dividend is owed to us, but hasn't been dispersed yet """
        next_dividend = next((div for div in self._dividends() if date < div["Date"]), None)
        past_dividend = next((div for div in reversed(self._dividends()) if date >= div["Date"]), None)

        return (self._calculate_yield_accrued(next_dividend, past_dividend, date)
                if next_dividend and past_dividend
                else self._estimate_yield_accrued(next_dividend, past_dividend, date))
