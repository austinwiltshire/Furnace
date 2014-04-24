""" Performance tracking """

# - equity curve (DONE)
# - cagr (DONE)
# - volatility
# - max drawdown

import numpy
import operator
import furnace.portfolio
from furnace.data import fcalendar
from furnace.filter import itertools_helpers, algorithm
import itertools

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

    def total_return(self):
        """ Returns the total return from begining to end """
        return reduce(operator.mul, [p.growth() for p in self._portfolio_periods])

    def duration(self):
        """ Returns the length of this performance period """
        #NOTE: looked at using dateutil.relativedelta here, but we actually want absolute number of days between
        #any two begin and end dates.
        return self._portfolio_periods[-1].end() - self._portfolio_periods[0].begin()

    def cagr(self):
        """ Returns the compound annual growth rate """
        return pow(self.total_return(), 1.0 / (self.duration().days / 365.0))

    def growth_by(self, date):
        """ Returns growth by a date as a percent scaled against 100% on beginning date of this performance """

        applicable_period = algorithm.find(self._portfolio_periods, lambda p: p.begin() <= date <= p.end())
        before_periods = [p for p in self._portfolio_periods if p.end() < date]
        growth_at_begin = reduce(operator.mul, [p.growth() for p in before_periods], 1.0)
        return growth_at_begin * applicable_period.growth_by(date)

    def plot_index(self, subplot, index_base):
        """ Plots a day by day performance on a matplotlib chart """

        dates = list(itertools.takewhile(lambda d: d <= self.end(), fcalendar.build_trading_date_rule(self.begin())))
        values = [index_base * self.growth_by(day) for day in dates]

        subplot.plot(numpy.array([numpy.datetime64(d) for d in dates]), numpy.array(values))

    def begin(self):
        """ Returns beginning date of this performance period """
        return sorted(self._portfolio_periods, cmp=lambda x, y: x.begin() < y.begin())[0].begin()

    def end(self):
        """ Returns ending date of this performance period """
        return sorted(self._portfolio_periods, cmp=lambda x, y: x.begin() < y.begin())[-1].end()

class PeriodPerformance(object):
    """ How a strategy does over it's trading period """

    def __init__(self, begin_portfolio, end_portfolio):
        self._begin_portfolio = begin_portfolio
        self._end_portfolio = end_portfolio

    def growth(self):
        """ Growth from begin to end period """
        return furnace.portfolio.growth(self._begin_portfolio, self._end_portfolio)

    def begin(self):
        """ Returns start date of this period """
        return self._begin_portfolio.date()

    def end(self):
        """ Return end date of this performance period """
        return self._end_portfolio.date()

    def overlaps_with(self, other):
        """ Returns true if this period overlaps with other period """
        return self.end() > other.begin() if self.begin() < other.begin() else other.end() > self.begin()

    def growth_by(self, date):
        """ Return growth as a percentage based on 100% at beginning of the period by date"""
        assert self.begin() <= date <= self.end()
        return furnace.portfolio.growth(self._begin_portfolio, self._begin_portfolio.on_date(date))
