""" Performance tracking """

import datetime
import scipy.stats.mstats
import numpy
import operator
import data
import weathermen
import portfolio

class Furnace:
    """ Our testing framework """
    def fire(self, strategy):
        """ Given a financial strategy, returns performance metrics for it """
        #the testing framework should just pass in, say, date ranges and it'd then remain period agnostic
        #once we have the date ranges, we can then ask the trading strategy what its periods would be, and generate the trading periods
        #we ultimately want - for a particular date (dates set by the periodicity), what are the holdings the strategy would advise
        #then what are the returns of those holdings over the period?

        performance = strategy.performance_during(datetime.date(2001, 1, 2), datetime.date(2012, 12, 31))

        #performance_measurements = []

        #for trading_period in strategy.periods_during(datetime.date(2001,1,2), datetime.date(2012,12,31)):
            #  a trading period needs to be a pair of dates so we can calculate return during the whole time. the simplest trading period would have
            # an ending date the same as the next period's begin date

            # the portfolios need to know their dates for metrics to be useful
        #    begin_portfolio = strategy.portfolio_on(trading_period.begin())
        #    end_portfolio = strategy.portfolio_on(trading_period.end())
#
#            performance_measurements.append(self.measure_performance(begin_portfolio, end_portfolio))


        #we want to pass a set of trading periods in with their inputs as we'd know them
        #and get the portfolio the strategy would hold back out
        #then we'd need to calculat the actual return for that portfolio
        #once we have the actual returns for the entire portfolio we can calculate metrics like:
        # - equity curve
        # - cagr
        # - volatility
        # - max drawdown

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
        #we know we're currently using daily's. Eventually we need to adjust this to basically take the overall growth and then divide it by the time.
        #these seem like things that should be known from the period performances.
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

