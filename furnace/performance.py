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
        return reduce(operator.mul, [p.total_return() for p in self._portfolio_periods])

    def duration(self):
        """ Returns the length of this performance period """
        #NOTE: looked at using dateutil.relativedelta here, but we actually want absolute number of days between
        #any two begin and end dates.
        return self._portfolio_periods[-1].end() - self._portfolio_periods[0].begin()

    def cagr(self):
        """ Returns the compound annual growth rate """
        return pow(self.total_return(), 1.0 / (self.duration().days / 365.0))

    #TODO: 
    # i think i don't need to adjust for dividends. they'll be adjusted by the
    # exchanges automatically. the price *drops* the day of the dividend by
    # precisely the same amount as the yield, so the return for that day
    # should overall be in line with what i expect. 
    # the only thing i *should* do is keep in mind if i create cap gains
    # separate models, there will be dividend effects on the div date that are
    # secular to any cap gains movements. so if i want to predict just cap
    # gains and dividends separately, i just need to account for that effect
    # there but not when it comes to simply plotting performance.
    #1. simple daily volatility over the entire period
    #   a. add daily return to asset. Given a date, i need to know the capital gains for that day as a % DONE
    #       i. need to figure out a lag DONE
    #   b. add daily basis adjustment to asset. Given a date, i need to know how much of a basis/yield I got assuming
    #       I accrue dividends on a daily basis and buy stock that day.
    #       Currently trying to figure out how to create a new column in a data frame that's the next dividend date.
    #       I'm able to get what I think is the correct date using the searchsorted function, feeding in dividend dates
    #       as the first argument, dropping the indexes past the length of the number of dividends. I do not know how to
    #       glue this new column as a series on to the old one. I think reindexing both to just integers would work?
    #   c. both of the above should be columns on asset's data frame
    #   d. portfolio's growth should simply be a multiplication of the above plus the addition of the basis/yield
    #   QUESTION: do i need a basis on asset or just a daily yield and daily cap gains, and portfolio will be the one
    #       that uses yield to grow basis and cap gains to adjust price?
    #   NOTE: all of this should not change mathematically the answers to what i've found so far so regression tests
    #       should still work even if i change the arithmatic. of course, some floating point error might be seen
    #2. paramaterize on sample length - do trailing daily volatility of only a few months (this moves the 'beginnign)
    #3. parameterize on window - given two dates, calculate weekly volatilty. (this moves the 'end')
    #4. parameterize on period length - do trailing weekly volatility
    #5. add parameterizations to cagr
    #6. use the new tables to speed up index generation
    def volatility(self):
        """ Returns the simple daily volatility of price movements, as a percent, of this entire performance period """
        #need to generate daily returns with dividend adjustments
        #TODO: below is pseudocode
    # index.table.pct_change().dropna() #this implies that one index's last day is another's first day!!!
#        return pd.volatility(pd.concat([period.table() for period in self._portfolio_periods]))
        #NOTE: http://wiki.fool.com/How_to_Calculate_the_Annualized_Volatility
        #daily volatility is the sqrt of period variance. this is annualized by multiplying it by number of trading
        #days in a year, commonly assumed by economists to be 252
        index = self._portfolio_periods[0].table()
        return numpy.sqrt(252*index.var())

    def growth_by(self, date):
        """ Returns growth by a date as a percent scaled against 100% on beginning date of this performance """

        applicable_period = algorithm.find(self._portfolio_periods, lambda p: p.begin() <= date <= p.end())
        before_periods = [period for period in self._portfolio_periods if period.end() < date]
        growth_at_begin = reduce(operator.mul, [period.growth() for period in before_periods], 1.0)
        return growth_at_begin * applicable_period.growth_by(date)

    def plot_index(self, subplot, index_base):
        """ Plots a day by day performance, with day one pegged at value of index_base, on a matplotlib chart """
        #NOTE: horribly inefficient. Some sort of memoization on growth_by would probably speed it up
        #NOTE: probably just head towards a eager rule when it comes to
        # prebuilding the performance tables.

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

    def total_return(self):
        """ Growth from begin to end period """
        return furnace.portfolio.total_return(self._begin_portfolio, self._end_portfolio)

    def table(self):
        """ Accessor for the index this period performance is based on """
        index = self._begin_portfolio.make_index().table
        index = index[index.index >= self.begin()][index.index <= self.end()]

        return index.pct_change().dropna()

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
        return furnace.portfolio.total_return(self._begin_portfolio, self._begin_portfolio.reinvest_dividends(date))
