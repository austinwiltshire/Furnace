""" For overall financial strategies - pairs of forecasters and portfolio optimizers """

# Ultimately the metrics forecasted as inputs for the optimizer are part of the financial strategy and may have
# different models for each one

from furnace import performance
from furnace import weathermen
from furnace import portfolio
from dateutil.rrule import rrule, YEARLY
import abc

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

class Strategy(object):
    """ A pair of weatherman and portfolio optimizer """
    __metaclass__ = abc.ABCMeta

    def __init__(self, portfolio_optimizer, asset_universe, rebalancing_rule, forecaster):
        self._portfolio_optimizer = portfolio_optimizer
        self._asset_universe = asset_universe
        self._rebalancing_rule = rebalancing_rule
        self._forecaster = forecaster

    def performance_during(self, begin_date, end_date):
        """ Gets the overall performance from begin_date to end_date """
        #NOTE: seems like this should live in Performance.py
        #NOTE: we might get rid of the whole notion of an 'ending' portfolio, and always assume that a beginning
        #portfolio and ending portfolio have the same *initial target* but differ in dividends reinvested

        #NOTE: turning off for now for great performance
        assert self._asset_universe.supports_date(begin_date)
        assert self._asset_universe.supports_date(end_date), "calendar does not support date {0}".format(end_date)

        period_performances = []
        for trading_period in self.periods_during(begin_date, end_date):
            period_begin = trading_period.begin()
            index = self.target_weighting_on(period_begin).make_index_on(period_begin)
            period_performances.append(performance.make_period_performance(period_begin, trading_period.end(), index))

        return performance.OverallPerformance(period_performances, self._asset_universe)

    def periods_during(self, begin_date, end_date):
        """ The periods this strategy operates on - i.e., weekly, monthly, daily """
        assert begin_date <= end_date

        return self._rebalancing_rule.periods_during(begin_date, end_date)

    def forecast(self, date):
        """ Generate a forecast for this strategy """
        return self._forecaster.forecast(self._asset_universe, date, self._rebalancing_rule.period_length())

    def target_weighting_on(self, date):
        """ Generates a target portfolio this strategy would recommend for date """

        forecast = self.forecast(date)
        return self._portfolio_optimizer.optimize(forecast, self._asset_universe)

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

    def __init__(self, begin_date, end_date):
        self._begin_date = begin_date
        self._end_date = end_date

    def periods_during(self, begin_date, end_date):
        """ Returns a single trading period: begin to end """
        assert begin_date <= end_date
        assert self._begin_date == begin_date
        assert self._end_date == end_date

        yield TradingPeriod(begin_date, end_date)

    def period_length(self):
        """ Returns the length of the buy and hold period """
        return (self._end_date - self._begin_date).days

class AnnualRebalance(RebalancingRule):
    """ Annual rebalance rebalances every year on same day as begin_date """

    def __init__(self, fcalendar):
        """ Requires a calendar to find future trading dates """
        self._fcalendar = fcalendar

#TODO: add test that we start our rebalance on correctly on the first day 
    def periods_during(self, begin_date, end_date):
        """ Returns all first trading dates of the year between begin and end date """

        dates = list(rrule(YEARLY, dtstart=begin_date, until=end_date))
        for period_begin, period_end in zip(dates[:-1], dates[1:]):
            yield TradingPeriod(self._fcalendar.nth_trading_day_after(0, period_begin),
                                self._fcalendar.nth_trading_day_after(0, period_end))

    def period_length(self):
        """ Returns a years length """
        return 365

class NDayRebalance(RebalancingRule):
    """ Rebalances every n days from begin date """

    def __init__(self, fcalendar, ndays):
        """ Requires a calendar to find future trading dates """
        self._fcalendar = fcalendar
        self._ndays = ndays

#TODO: should test that we end properly on the end date when it's viable
#TODO: should test that there are the right number of trading days and they are the right size for a known
#period
#TODO: test that we fall across weekends and holidays correctly
    def periods_during(self, begin_date, end_date):
        """ Iterates through every n days starting at begin date """

        dates = [date for date in self._fcalendar]
        current = dates.index(self._fcalendar.nth_trading_day_after(0, begin_date))
        end = dates.index(self._fcalendar.nth_trading_day_before(0, end_date))
        periods = zip(dates[current:end-self._ndays:self._ndays], dates[current + self._ndays:end:self._ndays])
        return (TradingPeriod(date1, date2) for date1, date2 in periods)

    def period_length(self):
        """ Returns a years length """
        return self._ndays

#family strategies
def buy_and_hold_single_asset(asset_universe, begin_date, end_date, symbol):
    """ Purchases a single asset at the beginning of the period and holds it to the end.
    Represents a family of potential strategies """

    assert asset_universe.supports_date(begin_date)
    assert asset_universe.supports_symbol(symbol)

    asset_universe = asset_universe.restricted_to([symbol])

    return Strategy(portfolio.SingleAsset(),
                    asset_universe,
                    BuyAndHold(begin_date, end_date),
                    weathermen.NullForecaster())

def buy_and_hold_multi_asset(asset_universe, begin_date, end_date, symbols, weights):
    """ Purchses a set of assets with specific weights at the beginning of the period and holds them to the end.
    Represents a family of buy and hold multi asset strategies that vary on asset mix and weights """

    assert asset_universe.supports_date(begin_date)

    assert all(asset_universe.supports_symbol(symbol) for symbol in symbols)
    weightings = portfolio.Weightings([portfolio.Weighting(asset_universe.make_asset(symbol), weight)
                                       for symbol, weight in zip(symbols, weights)])

    return Strategy(portfolio.StaticTarget(weightings),
                    asset_universe.restricted_to(symbols),
                    BuyAndHold(begin_date, end_date),
                    weathermen.NullForecaster())

def yearly_rebalance_single_asset(asset_universe, fcalendar, symbol):
    """ A single asset that is rebalanced. This is a no-op strategy used for testing """

    assert asset_universe.supports_symbol(symbol)

    asset_universe = asset_universe.restricted_to([symbol])

    return Strategy(portfolio.SingleAsset(),
                    asset_universe,
                    AnnualRebalance(fcalendar),
                    weathermen.NullForecaster())

def yearly_rebalance_multi_asset(asset_universe, fcalendar, symbols, weights):
    """ An annually rebalanced multi asset portfolio with static targets. """

    assert all(asset_universe.supports_symbol(symbol) for symbol in symbols)
    weightings = portfolio.Weightings([portfolio.Weighting(asset_universe.make_asset(symbol), weight)
                                       for symbol, weight in zip(symbols, weights)])

    return Strategy(portfolio.StaticTarget(weightings),
                    asset_universe.restricted_to(symbols),
                    AnnualRebalance(fcalendar),
                    weathermen.NullForecaster())

def ndays_rebalance_single_asset(asset_universe, fcalendar, symbol, days):
    """ A single asset that is rebalanced. This is a no-op strategy used for testing """

    assert asset_universe.supports_symbol(symbol)

    asset_universe = asset_universe.restricted_to([symbol])

    return Strategy(portfolio.SingleAsset(),
                    asset_universe,
                    NDayRebalance(fcalendar, days),
                    weathermen.NullForecaster())

def ndays_rebalance_multi_asset(asset_universe, fcalendar, symbols, weights, days):

    assert all([asset_universe.supports_symbol(symbol) for symbol in symbols])

    weightings = portfolio.Weightings([portfolio.Weighting(asset_universe.make_asset(symbol), weight)
                                       for symbol, weight in zip(symbols, weights)])

    return Strategy(portfolio.StaticTarget(weightings),
                    asset_universe,
                    NDayRebalance(fcalendar, days),
                    weathermen.NullForecaster())

#particular strategies
def buy_and_hold_stocks(asset_universe, begin_date, end_date):
    """ Purchases the SPY at the beginning period and holds it to the end """
    return buy_and_hold_single_asset(asset_universe, begin_date, end_date, "SPY")

def buy_and_hold_bonds(asset_universe, begin_date, end_date):
    """ Purchases the LQD at the beginning period and holds it to the end """
    return buy_and_hold_single_asset(asset_universe, begin_date, end_date, "LQD")

def buy_and_hold_stocks_and_bonds(asset_universe, begin_date, end_date):
    """ Purchases 80% SPY and 20% LQD """
    return buy_and_hold_multi_asset(asset_universe, begin_date, end_date, ["SPY", "LQD"], [.8, .2])
