""" Performance tracking """

# - equity curve
# - cagr
# - volatility
# - max drawdown


import datetime
import numpy
import operator
import data
import weathermen
import portfolio

class Furnace:
    """ Our testing framework """
    def fire(self, strategy):
        """ Given a financial strategy, returns performance metrics for it """
        performance = strategy.performance_during(datetime.date(2001, 1, 2), datetime.date(2012, 12, 31))

        return performance

class OverallPerformance:
    """ OverallPerformance is how a strategy does over time. """

    def __init__(self, portfolio_periods):
        """ Currently expects a dict of dates to portfolios """
        self._portfolio_periods = portfolio_periods

    def total_return(self):
        """ Returns the total return from begining to end """
        return reduce(operator.mul, [p.growth() for p in self._portfolio_periods])

    def years(self):
        """ Number of years in performance period """
        days = (self._portfolio_periods[-1].end() - self._portfolio_periods[0].begin()).days
        return days / 365.0

    def CAGR(self):
        """ Returns the compound annual growth rate """
        return pow(self.total_return(), 1.0 / self.years())

class PeriodPerformance:
    """ How a strategy does over it's trading period """

    def __init__(self, begin_portfolio, end_portfolio):
        self._begin_portfolio = begin_portfolio
        self._end_portfolio = end_portfolio

    def growth(self):
        """ Growth from begin to end period """
        return portfolio.growth(self._begin_portfolio, self._end_portfolio)

    def begin(self):
        """ Returns start date of this period """
        return self._begin_portfolio.date()

    def end(self):
        """ Return end date of this performance period """
        return self._end_portfolio.date()

class PeriodPerformanceMetrics(object):
    """ Currently just CAGR """
    pass

