""" For overall financial strategies - pairs of forecasters and portfolio optimizers """

# Ultimately the metrics forecasted as inputs for the optimizer are part of the financial strategy and may have
# different models for each one

from furnace import performance
from furnace import weathermen
from furnace import portfolio
import datetime
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
        assert self._asset_universe.supports_date(begin_date)
        assert self._asset_universe.supports_date(end_date)

        period_performances = []
        for trading_period in self.periods_during(begin_date, end_date):
            period_begin = trading_period.begin()
            beginning_portfolio = self.target_portfolio_on(period_begin).unit_portfolio(period_begin)
            end_portfolio = beginning_portfolio.on_date(trading_period.end())
            period_performances.append(performance.PeriodPerformance(beginning_portfolio, end_portfolio))
        return performance.OverallPerformance(period_performances)

    def periods_during(self, begin_date, end_date):
        """ The periods this strategy operates on - i.e., weekly, monthly, daily """
        assert begin_date <= end_date

        return self._rebalancing_rule.periods_during(begin_date, end_date)

    def forecast(self, date):
        """ Generate a forecast for this strategy """
        return self._forecaster.forecast(self._asset_universe, date, self._rebalancing_rule.period_length())

    def target_portfolio_on(self, date):
        """ Generates a target portfolio this strategy would recommend for date """

        forecast = self.forecast(date)
        return self._portfolio_optimizer.optimize(forecast)

#NOTE: assuming there will be more rebalancing rules eventually and this interface will grow
#pylint: disable=R0922,R0903
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

#NOTE: assumed this interface will grow
#pylint: disable=R0903
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

#pylint: enable=R0903


#TODO: this strategy is a static portfolio target of 100% one asset and a buy and hold trading period
# REFACTOR
#NOTE: i don't know how this works exactly yet, but if a portfolio is just a target generator, a trading period
#and an *asset universe* (i.e., which assets we'll hold), as well as possibly different optimization rules...
# optimization metrics (i.e., sharpe ratio), forecasting methods for each metric for each asset, asset universe
# and trading period
def buy_and_hold_stocks(asset_universe, begin_date, end_date):
    """ Purchases the SPY at the beginning period and holds it to the end """

    assert asset_universe.supports_date(begin_date)
    assert asset_universe.supports_symbol("SPY")

    asset_universe = asset_universe.restricted_to(["SPY"])

    return Strategy(portfolio.SingleAsset(asset_universe),
                    asset_universe,
                    BuyAndHold(begin_date, end_date),
                    weathermen.NullForecaster())

#TODO: NOW!!!!!
#next step:
#- add static target portfolio where the init takes in a target and it just always recommends that
#- pass in classes for portfolio and forecaster so that their asset universe arguments are always the same

#TODO: This stratey really is just a static portfolio target and a buy and hold trading period
#REFACTOR
def buy_and_hold_stocks_and_bonds(asset_universe, begin_date, end_date):
    """ Purchases 80% SPY and 20% LQD """

    assert asset_universe.supports_date(begin_date)
    assert asset_universe.supports_symbol("SPY")
    assert asset_universe.supports_symbol("LQD")

    return Strategy(portfolio.MixedBuyAndHold(asset_universe),
                    asset_universe.restricted_to(["SPY", "LQD"]),
                    BuyAndHold(begin_date, end_date),
                    weathermen.NullForecaster())
