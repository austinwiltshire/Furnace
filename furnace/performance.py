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

    #TODO: 
    #1. simple daily volatility over the entire period
    #   a. add daily return to asset. Given a date, i need to know the capital gains for that day as a %
    #   b. add daily basis adjustment to asset. Given a date, i need to know how much of a basis/yield I got assuming
    #       I accrue dividends on a daily basis and buy stock that day.
    #   c. both of the above should be columns on asset's data frame
    #   d. portfolio's growth should simply be a multiplication of the above plus the addition of the basis/yield
    #   QUESTION: do i need a basis on asset or just a daily yield and daily cap gains, and portfolio will be the one
    #       that uses yield to grow basis and cap gains to adjust price?
    #2. paramaterize on sample length - do trailing daily volatility of only a few months (this moves the 'beginnign)
    #3. parameterize on window - given two dates, calculate weekly volatilty. (this moves the 'end')
    #4. parameterize on period length - do trailing weekly volatility
    #5. add parameterizations to cagr
    def volatility(self):
        """ Returns the simple daily volatility of price movements, as a percent, of this entire performance period """
        #Should I just make a simplifying assumption that all statistics will ultimately be built off of daily deltas?
        #This would not only speed up the generation of indecies, but make these sorts of statistics trivial to
        #implement in pandas.
        #Pros:
        #   - Speed up generation of indecies. Equivalent to a memoization approach. Indexes generated daily anyway.
        #   - Easy to extend using pandas
        #Cons:
        #   - Settling on day is going to make going to subday intervals harder
        #   - Seems inelegant. But why?
        #Notes:
        #   - So long as periods longer than a day; i.e., strides; are still well supported (which i will implement and
        # test for using monthly and weekly rebalancing rules), a lot of the inelegance argument goes away
        #   - Will probably have a hard time going to sub day plots anyway, nor do I ultimately think I need sub day
        # plots any time soon anyway.
        #   - The design being discussed more or less means I will use my strategy to generate a time series of % deltas
        # possibly with other costs as well. Fitting it into the time series domain seems like I better leverage my
        # tools.
        #   - But I still intuitively don't like it. The parameterized approach that grabs things lazily seems more
        # 'closed form'. How I think of solving any particular problem is how it ultimately is solved rather than
        # consulting some sort of table.
        #   - Where will this table live? Probably in the period performance for now. OverallPerformance could
        # potentially be simplified into doing little more than stitching together various period performance time
        # series.
        #   - Thus the striding and windowing is still done at the period performance layer, which does continue to give
        # a bit of elegance back and fits with the rebalancing rule requirements.
        #   - There's really no other way.


        pass

    def growth_by(self, date):
        """ Returns growth by a date as a percent scaled against 100% on beginning date of this performance """

        applicable_period = algorithm.find(self._portfolio_periods, lambda p: p.begin() <= date <= p.end())
        before_periods = [period for period in self._portfolio_periods if period.end() < date]
        growth_at_begin = reduce(operator.mul, [period.growth() for period in before_periods], 1.0)
        return growth_at_begin * applicable_period.growth_by(date)

    def plot_index(self, subplot, index_base):
        """ Plots a day by day performance, with day one pegged at value of index_base, on a matplotlib chart """
        #NOTE: horribly inefficient. Some sort of memoization on growth_by would probably speed it up

        dates = list(itertools.takewhile(lambda date: date <= self.end(),
                     fcalendar.build_trading_date_rule(self.begin())))

        indecies = [index_base * self.growth_by(day) for day in dates]

        subplot.plot(numpy.array([numpy.datetime64(d) for d in dates]), numpy.array(indecies))

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
        return furnace.portfolio.growth(self._begin_portfolio, self._begin_portfolio.reinvest_dividends(date))
