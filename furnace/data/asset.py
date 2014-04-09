""" Creates the asset abstraction which gives an OO interface to price data. Care must be taken to ensure this is
    efficient in non OO / relational contexts, and that it gives relational metaphors when those make sense. Indeed,
    an asset might be better looked at as a table, rather than a pure OO abstraction. It represents all price data,
    not just one day's worth """

import operator
import numpy
from furnace.data import fcalendar
import pandas
import datetime

class AssetFactory(object):
    def __init__(self, data_cache, data_cache_pandas):
        self._data_cache = data_cache
        self._data_cache_pandas = data_cache_pandas

    def make_asset(self, symbol):
        """ Creates an asset based on the ticker symbol """
        return Asset(symbol, self._data_cache, self._data_cache_pandas)
class Asset(object):
    """ Represents a tradable security, by symbol """
    def __init__(self, symbol, data_cache, data_cache_pandas):
        self._symbol = symbol
        self._data_cache = data_cache
        self._data_cache_pandas = data_cache_pandas

    def _dividends(self):
        """ List of all available dividends """
        return sorted([div for div in self._data_cache[self._symbol]["dividends"].itervalues()],
                          key=lambda d: d["Date"])

    def _all_pandas(self):
        """ A concatenated list of dividends and prices in pandas format """
        return self._data_cache_pandas[self._symbol]["all"]

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

        assert date in fcalendar.ALL_TRADING_DAYS
        assert self._first_price_date() <= date <= self._last_price_date()

        return self._data_cache[self._symbol]["price"][date]["Close"]

    def average_yield(self):
        """ Returns the average dividend yield on a *per dividend* basis for this asset
            This is not annualized, nor is it geometric! """

        dividends = self._all_pandas()[["Dividends", "Close"]].dropna()
        return numpy.average(dividends["Dividends"] / dividends["Close"])

    def average_dividend_period(self):
        """ Returns the average period between dividends dispersals for this asset in days"""

        day = numpy.timedelta64(datetime.timedelta(1))
        average_period = numpy.average(self._all_pandas()["Dividends"].dropna().index.to_series().diff(1).dropna())
        return average_period / day

    def yield_between(self, begin, end):
        """ Returns the dividend yield (raw dividends / share price at the time) between begin and end """
        assert begin <= end, "Beginning date should happen before or during end date"

        dividends = self._all_pandas()[["Dividends", "Close"]].dropna()
        clamped_dividends = dividends[(dividends.index > begin) & (dividends.index <= end)]
        yields = (clamped_dividends["Dividends"] / clamped_dividends["Close"]) + 1.0
        return reduce(operator.mul, yields, 1.0) - 1.0

    def _expected_daily_accrued_yield(self):
        """ Returns the expected daily, non compounded, yield of this asset """
        return self.average_yield() / self.average_dividend_period()

    def _calculate_yield_accrued(self, next_dividend, past_dividend, date):
        """ Calculates the portion of the dividend yield accrued on date assuming both dividends are valid """
        assert not (next_dividend.empty or past_dividend.empty)

        days_between = float((next_dividend["Date"] - past_dividend["Date"]).days)
        yield_ = next_dividend["Dividends"] / self._all_pandas().ix[date]["Close"]
        days_in = float((date - past_dividend["Date"]).days)

#        import code
#        code.interact(local=locals())

        return days_in / days_between * yield_

    def _estimate_yield_accrued(self, next_dividend, past_dividend, date):
        """ Estimates the yield accrued between dividends when one is not available """
        assert next_dividend.empty or past_dividend.empty

        days_in = ((date - past_dividend["Date"]).days
                   if next_dividend.empty
                   else self.average_dividend_period() - (next_dividend["Date"] - date).days)

        if days_in > self.average_dividend_period() or days_in < 0.0:
            raise Exception("Too late or early to estimate dividends")

        return days_in * self._expected_daily_accrued_yield()

    def yield_accrued(self, date):
        """ Returns the yield accrued to this asset to date. Accrued means dividend is owed to us but has not
        been dispersed yet."""

        one_day = datetime.timedelta(1)

        #NOTE: past_dividend is inclusive, i.e., if today is dividend issue date, we consider it past.
        next_dividend = self._all_pandas()["Dividends"].dropna().ix[date+one_day:].reset_index()
        if not next_dividend.empty:
            next_dividend = next_dividend.iloc[0]
        past_dividend = self._all_pandas()["Dividends"].dropna().ix[:date].reset_index()
        if not past_dividend.empty:
            past_dividend = past_dividend.iloc[-1]

        return (self._calculate_yield_accrued(next_dividend, past_dividend, date)
                if not next_dividend.empty and not past_dividend.empty
                else self._estimate_yield_accrued(next_dividend, past_dividend, date))
