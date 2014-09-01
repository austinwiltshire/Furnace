""" Performance tracking """

# - equity curve (DONE)
# - cagr (DONE)
# - volatility (DONE)
# - max drawdown

import numpy
from furnace.filter import itertools_helpers
import pandas

#NOTE: this used to be a single method on an object. Would make sense to refactor to that if we need to add more state
#to our simulation
def fire_furnace(strategy, begin_date, end_date):
    """ Given a financial strategy, returns performance metrics for it """
    return strategy.performance_during(begin_date, end_date)

class OverallPerformance(object):
    """ OverallPerformance is how a strategy does over time. """

    def __init__(self, portfolio_periods):
        """ Currently expects a dict of dates to portfolios """
        self._portfolio_periods = portfolio_periods
        assert sorted(portfolio_periods, key=PeriodPerformance.begin) == portfolio_periods
        assert not any(itertools_helpers.self_cartesian_map(portfolio_periods, PeriodPerformance.overlaps_with))
        self._table = pandas.DataFrame()
        self._table["Daily Returns"] = pandas.concat(period.daily_returns() for period in self._portfolio_periods)
        self._table["Cumulative Returns"] = (self._table["Daily Returns"] + 1.0).cumprod()
        #import IPython
        #IPython.embed()

    def total_return(self):
        """ Returns the total return from begining to end """
        return self.growth_by(self.end())

    def duration(self):
        """ Returns the length of this performance period """
        #NOTE: looked at using dateutil.relativedelta here, but we actually want absolute number of days between
        #any two begin and end dates.
        return self._portfolio_periods[-1].end() - self._portfolio_periods[0].begin()

    def cagr(self):
        """ Returns the compound annual growth rate """
        return pow(self.total_return(), 1.0 / (self.duration().days / 365.0))

    def volatility(self):
        """ Returns the simple daily volatility of price movements, as a percent, of this entire performance period """
        #NOTE: http://wiki.fool.com/How_to_Calculate_the_Annualized_Volatility
        #daily volatility is the sqrt of period variance. this is annualized by multiplying it by number of trading
        #days in a year, commonly assumed by economists to be 252
        return numpy.sqrt(252*self._table["Daily Returns"].var())

    def growth_by(self, date):
        """ Returns growth by a date as a percent scaled against 100% on beginning date of this performance """
        if date == self.begin():
            return 1.0
        return self._table["Cumulative Returns"][date]

    def plot_index(self, index_base):
        """ Plots a day by day performance, with day one pegged at value of index_base, on a matplotlib chart """

        indecies = self._table["Cumulative Returns"] * index_base
        return indecies.plot()

    def begin(self):
        """ Returns beginning date of this performance period """
        return sorted(self._portfolio_periods, cmp=lambda x, y: x.begin() < y.begin())[0].begin()

    def end(self):
        """ Returns ending date of this performance period """
        return sorted(self._portfolio_periods, cmp=lambda x, y: x.begin() < y.begin())[-1].end()

def make_period_performance(begin_date, end_date, index):
    """ Factory for a period performance object """

    begin = begin_date

    index = index.table
    index = index[index.index >= begin][index.index <= end_date]
    table = pandas.DataFrame()
    table["Daily Returns"] = index.pct_change().dropna()
    return PeriodPerformance(begin, end_date, table)

class PeriodPerformance(object):
    """ How a strategy does over it's trading period """

    def __init__(self, begin_date, end_date, table):
        self._begin_date = begin_date
        self._end_date = end_date
        self._table = table

    def daily_returns(self):
        """ Returns a daily series of this period's returns """
        return self._table["Daily Returns"]

    def begin(self):
        """ Returns start date of this period """
        return self._begin_date

    def end(self):
        """ Return end date of this performance period """
        return self._end_date

    def overlaps_with(self, other):
        """ Returns true if this period overlaps with other period """
        return self.end() > other.begin() if self.begin() < other.begin() else other.end() > self.begin()
