""" For overall financial strategies - pairs of forecasters and portfolio optimizers """

# Ultimately the metrics forecasted as inputs for the optimizer are part of the financial strategy and may have
# different models for each one

from furnace import performance
from furnace import weathermen
from furnace import portfolio
from dateutil.rrule import rrule, YEARLY
import datetime
import abc
import furnace.data.fcalendar
from furnace.data.fcalendar import first_day_after
import furnace.data.yahoo
import furnace.data.asset

class TradingPeriod(object):
    """ The begining and end of an entire trading period on which metrics can be collected """
    def __init__(self, begin, end):
        self._begin = begin
        self._end = end

    def begin(self):
        """ Getter for the beginning of this trading period """
        return self._begin

    def end(self):
        """ Getter for the end of this trading period """
        return self._end

    def trading_days(self, calendar):
        """ Returns the number of trading days in this period using calendar """
        return calendar.number_trading_days_between(self._begin, self._end)

class Strategy(object):
    """ A pair of weatherman and portfolio optimizer """
    __metaclass__ = abc.ABCMeta

    def __init__(self, portfolio_optimizer, asset_universe, rebalancing_rule, forecaster):
        self._portfolio_optimizer = portfolio_optimizer
        self._universe = asset_universe
        self._rebalancing_rule = rebalancing_rule
        self._forecaster = forecaster

    def performance_during(self, begin_date, end_date):
        """ Gets the overall performance from begin_date to end_date """
        assert self._universe.supports_date(begin_date)
        assert self._universe.supports_date(end_date), "calendar does not support date {0}".format(end_date)

        period_performances = []
        for trading_period in self.periods_during(begin_date, end_date):
            period_begin = trading_period.begin()
            index = self.target_weighting_on(period_begin).make_index_on(period_begin, trading_period.end())
            period_performances.append(performance.make_period_performance(period_begin, trading_period.end(), index))

        return performance.make_overall_performance(period_performances, self._universe)

    def periods_during(self, begin_date, end_date):
        """ The periods this strategy operates on - i.e., weekly, monthly, daily """
        assert begin_date <= end_date

        return self._rebalancing_rule.periods_during(begin_date, end_date)

    def forecast(self, date):
        """ Generate a forecast for this strategy """
        return self._forecaster(self._universe, date, self._rebalancing_rule.period_length())

    def target_weighting_on(self, date):
        """ Generates a target portfolio this strategy would recommend for date """

        forecast = self.forecast(date)
        return self._portfolio_optimizer.optimize(forecast, self._universe)

#NOTE: assuming there will be more rebalancing rules eventually and this interface will grow
#pylint: disable=R0922
class RebalancingRule(object):
    """ Represents different strategies for when to rebalance a portfolio """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def periods_during(self, begin_date, end_date):
        """ Returns a set of periods, beginning at begin and ending at end (possibly truncated at beginning and end)
            based on this rebalancing rule with rebalancing to occur at each period switch """
        pass

    @abc.abstractmethod
    def period_length(self):
        """ The length of time in days of this period """
        pass
#pylint: enable=R0922

class BuyAndHold(RebalancingRule):
    """ Buy and hold never trades - it starts with its beginning portfolio and holds it until the end """

    def __init__(self, begin_date, end_date, fcalendar):
        assert begin_date <= end_date
        self._begin_date = begin_date
        self._end_date = end_date
        self._fcalendar = fcalendar

    def periods_during(self, begin_date, end_date):
        """ Returns a single trading period: begin to end """
        assert begin_date <= end_date
        assert self._begin_date == begin_date
        assert self._end_date == end_date

        yield TradingPeriod(begin_date, end_date)

    def period_length(self):
        """ Returns the length of the buy and hold period """
        return self._fcalendar.number_trading_days_between(self._begin_date, self._end_date)

class AnnualRebalance(RebalancingRule):
    """ Annual rebalance rebalances every year on same day as begin_date """

    def __init__(self, fcalendar):
        """ Requires a calendar to find future trading dates """
        self._fcalendar = fcalendar

    def periods_during(self, begin_date, end_date):
        """ Returns all first trading dates of the year between begin and end date """

        dates = list(rrule(YEARLY, dtstart=begin_date, until=end_date))
        for period_begin, period_end in zip(dates[:-1], dates[1:]):
            yield TradingPeriod(first_day_after(self._fcalendar, period_begin),
                                first_day_after(self._fcalendar, period_end))

    def period_length(self):
        """ Returns a years length in real days. Period length would generally find the closest trading day to one year
        out """
        return furnace.data.fcalendar.trading_days_in_year()

class NDayRebalance(RebalancingRule):
    """ Rebalances every n days TRADING from begin date """

    def __init__(self, fcalendar, ndays):
        """ Requires a calendar to find future trading dates """
        self._fcalendar = fcalendar
        self._ndays = ndays

    def periods_during(self, begin_date, end_date):
        """ Iterates through every n days starting at begin date """
        periods = self._fcalendar.every_nth_between(begin_date, end_date, self._ndays)
        periods = zip(periods[:-1], periods[1:])

        periods = [TradingPeriod(date1, date2) for date1, date2 in periods]
        assert all(tp.trading_days(self._fcalendar) == self._ndays for tp in periods)
        return periods

    def period_length(self):
        """ Returns the trading days """
        return self._ndays

#TODO: look at eliminating most of these and decomposing common helpers out of them, DRY this up
#family strategies
def buy_and_hold_single_asset(universe, begin_date, end_date, asset, fcalendar):
    """ Purchases a single asset at the beginning of the period and holds it to the end.
    Represents a family of potential strategies """

    assert universe.supports_date(begin_date)
    assert universe.cardinality() == 1
    assert universe.supports_symbol(asset.symbol())

    return Strategy(portfolio.SingleAsset(asset),
                    universe,
                    BuyAndHold(begin_date, end_date, fcalendar),
                    weathermen.null_forecaster())

#TODO: i hate these methods but i'm not sure how to avoid them.
#I'd like to pull any of their uses out of anything but test_strategy subsidiaries,
#perhaps use a factory to remove the universe and fcalendar requirements,
#and then dry up anything remaining
def buy_and_hold_multi_asset(universe, begin_date, end_date, weights, fcalendar):
    """ Purchses a set of assets with specific weights at the beginning of the period and holds them to the end.
    Represents a family of buy and hold multi asset strategies that vary on asset mix and weights """

    assert universe.supports_date(begin_date)

    weightings = portfolio.Weightings([portfolio.Weighting(universe[symbol], weight)
                                       for symbol, weight in weights.iteritems()])

    return Strategy(portfolio.StaticTarget(weightings),
                    universe,
                    BuyAndHold(begin_date, end_date, fcalendar),
                    weathermen.null_forecaster())

def yearly_rebalance_single_asset(universe, fcalendar, symbol):
    """ A single asset that is rebalanced. This is a no-op strategy used for testing """

    assert universe.supports_symbol(symbol)

    return Strategy(portfolio.SingleAsset(universe[symbol]),
                    universe,
                    AnnualRebalance(fcalendar),
                    weathermen.null_forecaster())

def yearly_rebalance_multi_asset(universe, fcalendar, weightings):
    """ An annually rebalanced multi asset portfolio with static targets. """

    weightings = portfolio.Weightings([portfolio.Weighting(universe[symbol], weight)
                                       for symbol, weight in weightings.iteritems()])

    return Strategy(portfolio.StaticTarget(weightings),
                    universe,
                    AnnualRebalance(fcalendar),
                    weathermen.null_forecaster())

def ndays_rebalance_single_asset(universe, fcalendar, symbol, days):
    """ A single asset that is rebalanced. This is a no-op strategy used for testing """

    assert universe.supports_symbol(symbol)

    return Strategy(portfolio.SingleAsset(universe[symbol]),
                    universe,
                    NDayRebalance(fcalendar, days),
                    weathermen.null_forecaster())

def ndays_rebalance_multi_asset(universe, fcalendar, weights, days):
    """ A multi asset portfolio that is rebalanced every n days """

    weightings = portfolio.Weightings([portfolio.Weighting(universe[key], weight)
                                       for key, weight in weights.iteritems()])

    return Strategy(portfolio.StaticTarget(weightings),
                    universe,
                    NDayRebalance(fcalendar, days),
                    weathermen.null_forecaster())

def buy_and_hold_stocks(universe, begin_date, end_date, fcalendar):
    """ Purchases the SPY at the beginning period and holds it to the end """
    spy = universe["SPY"]
    return buy_and_hold_single_asset(universe, begin_date, end_date, spy, fcalendar)

def buy_and_hold_stocks_and_bonds(universe, begin_date, end_date, fcalendar):
    """ Purchases 80% SPY and 20% LQD """
    return buy_and_hold_multi_asset(universe, begin_date, end_date, {"SPY": .8, "LQD": .2}, fcalendar)

def v1_baseline():
    """ Builds a strategy that is currently the best of breed as of Oct 26 2014. This is a 20% stocks, 80% bonds
    strategy that rebalances every 25 trading days. """

    begin = datetime.datetime(2003, 1, 2)
    end = datetime.datetime(2012, 12, 31)
    calendar = furnace.data.fcalendar.make_fcalendar(datetime.datetime(2000, 1, 1))
    data_cache = furnace.data.yahoo.load_pandas()
    asset_factory = furnace.data.asset.Factory(data_cache, calendar)
    universe = asset_factory.make_universe(["SPY", "LQD"])

    strategy = ndays_rebalance_multi_asset(universe, calendar, {"SPY": .2, "LQD": .8}, 25)
    return strategy.performance_during(begin, end)
