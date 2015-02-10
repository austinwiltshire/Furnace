""" Performance tracking """

import numpy
import pandas
import datetime
import itertools
import furnace.data.fcalendar

def make_overall_performance(portfolio_periods, asset_universe):
    """ Factory function to create overall performances """

    table = pandas.DataFrame()
    table["Daily Returns"] = pandas.concat(period.daily_returns() for period in portfolio_periods)
    table["Cumulative Returns"] = ((table["Daily Returns"] + 1.0).cumprod() - 1.0)

    return OverallPerformance(portfolio_periods, asset_universe, table)

class OverallPerformance(object):
    """ OverallPerformance is how a strategy does over time. """

    def __init__(self, portfolio_periods, asset_universe, table):
        """ Currently expects a dict of dates to portfolios. Period performances are inclusive of end
        dates and exclusive of begin dates. That means altogether, they're inclusive of the entire trading
        period and it's end and exclusive of it's end. We have a single special case to handle that in
        overall performance. """
        self._portfolio_periods = portfolio_periods
        self._asset_universe = asset_universe
        self._table = table

        self.__invariant()

    def __invariant(self):
        """ Object invariants. This adds about a second to testing and can be turned off """
        assert sorted(self._portfolio_periods, key=PeriodPerformance.begin) == self._portfolio_periods
        assert not any(
            period1.overlaps_with(period2)
            for period1, period2 in itertools.product(self._portfolio_periods, self._portfolio_periods)
            if period1 is not period2
        )

    def total_return(self):
        """ Returns the total return from begining to end """
        self.__invariant()
        return self.growth_by(self.end())

#TODO: add assertion that len(self._table.index) == number of trading days between begin and end in financial calendar
#TODO: to do the above i'd need to pass in a fcalendar 
    def duration(self):
        """ Returns the length of this performance period in trading days"""
        self.__invariant()
        return datetime.timedelta(len(self._table.index))

    def cagr(self):
        """ Returns the compound annual growth rate """
        self.__invariant()
        return pow(
            1.0 + self.total_return(),
            1.0 / (self.duration().days / furnace.data.fcalendar.trading_days_in_year())
        ) - 1.0

    def expected_return(self):
        """ Returns the expected daily return """
        self.__invariant()
        return self._table["Daily Returns"].mean()

    def volatility(self):
        """ Returns the simple daily volatility of price movements, as a percent, of this entire performance period """
        self.__invariant()
        #NOTE: http://wiki.fool.com/How_to_Calculate_the_Annualized_Volatility
        return numpy.sqrt(furnace.data.fcalendar.trading_days_in_year()*self._table["Daily Returns"].var())

    def growth_by(self, date):
        """ Returns growth by a date as a percent on beginning date of this performance """
        self.__invariant()
        if date == self.begin():
            return 0.0
        return self._table["Cumulative Returns"][date]

    def plot_index(self, index_base):
        """ Plots a day by day performance, with day one pegged at value of index_base, on a matplotlib chart """
        self.__invariant()

        indecies = (1.0 + self._table["Cumulative Returns"]) * index_base
        return indecies.plot()

    def begin(self):
        """ Returns beginning date of this performance period """
        self.__invariant()
        return self._portfolio_periods[0].begin()

    def end(self):
        """ Returns ending date of this performance period """
        self.__invariant()
        return self._portfolio_periods[-1].end()

    def simple_sharpe(self):
        """ Returns a simplified sharpe ratio - cagr over volatility. """
        self.__invariant()
        return self.cagr() / self.volatility()

    #TODO: add test on this.
    #FIXME: cardinality no longer is a useful idea on the 'asset universe'.
    #FIXME: yep, cardinality is now officially a bug.
    def number_of_trades(self):
        """ Simple turnover metric - an estimate of the number of trades we make """
        self.__invariant()
        return len(self._portfolio_periods) * self._asset_universe.cardinality()

def make_period_performance(begin_date, end_date, index):
    """ Factory for a period performance object """
    #NOTE: due to pct diff taking N points and returning N-1 points, a period perfomance
    #of returns is inclusive of the end date but exclusive of the begin date

    begin = begin_date

    index = index.table
    index = index[index.index >= begin][index.index <= end_date]
    table = pandas.DataFrame()

    table["Daily Returns"] = index.pct_change().dropna()
    return PeriodPerformance(begin, end_date, table)

class PeriodPerformance(object):
    """ How a strategy does over it's trading period. A period performance is exclusive of it's begin
    date and inclusive of it's end date. In other words, if we had a period performance that started
    today, the soonest we'd have data available is tomorrow since today is our 'buy' point
    Our performance today, for example, is always 0%. """

    def __init__(self, begin_date, end_date, table):
        self._begin_date = begin_date
        self._end_date = end_date
        self._table = table

    def daily_returns(self):
        """ Returns a daily series of this period's returns """
        return self._table["Daily Returns"]

    def number_of_days(self):
        """ Returns number of trading days in this period """
        return len(self._table)

    def begin(self):
        """ Returns start date of this period """
        return self._begin_date

    def end(self):
        """ Return end date of this performance period """
        return self._end_date

    def overlaps_with(self, other):
        """ Returns true if this period overlaps with other period """
        return self.end() > other.begin() if self.begin() < other.begin() else other.end() > self.begin()
