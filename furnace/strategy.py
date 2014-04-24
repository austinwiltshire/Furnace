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

    def __init__(self, portfolio_optimizer, asset_factory):
        self._portfolio_optimizer = portfolio_optimizer
        self._asset_factory = asset_factory

    def performance_during(self, begin_date, end_date):
        """ Gets the overall performance from begin_date to end_date """
        assert self._asset_factory.supports(begin_date)
        assert self._asset_factory.supports(end_date)

        period_performances = []
        for trading_period in self.periods_during(begin_date, end_date):
            beginning_portfolio = self.portfolio_on(trading_period.begin())
            end_portfolio = beginning_portfolio.on_date(trading_period.end())
            period_performances.append(performance.PeriodPerformance(beginning_portfolio, end_portfolio))
        return performance.OverallPerformance(period_performances)

    @abc.abstractmethod
    def periods_during(self, begin_date, end_date):
        """ The periods this strategy operates on - i.e., weekly, monthly, daily """
        pass

    @abc.abstractmethod
    def forecast(self, date):
        """ Generate a forecast for this strategy """
        pass

    def portfolio_on(self, date):
        """ Generates a portfolio this strategy would recommend for date """

        forecast = self.forecast(date)
        portfolio_ = self._portfolio_optimizer.optimize(forecast, date)
        return portfolio_

#TODO: this strategy is a static portfolio target of 100% one asset and a buy and hold trading period
# REFACTOR
#NOTE: i don't know how this works exactly yet, but if a portfolio is just a target generator, a trading period
#and an *asset universe* (i.e., which assets we'll hold), as well as possibly different optimization rules...
# optimization metrics (i.e., sharpe ratio), forecasting methods for each metric for each asset, asset universe
# and trading period
class BuyAndHoldStocks(Strategy):
    """ Purchases the SPY at the begining period and holds it to the end """

    def __init__(self, asset_factory, begin_date):
        super(BuyAndHoldStocks, self).__init__(portfolio.BuyAndHoldPortfolio(begin_date), asset_factory)
        assert asset_factory.supports(begin_date)
        self._asset_factory = asset_factory
        self._begin_date = begin_date

    def periods_during(self, begin_date, end_date):
        """ Buy and hold only has one single period """
        assert begin_date >= self._begin_date

        yield TradingPeriod(begin_date, end_date)

    def forecast(self, date):
        """ We only trade in one asset so we only forecast one asset's growth """
        forecaster = weathermen.NullForecaster()
        return [forecaster.forecast(self._asset_factory.make_asset("SPY"), date, datetime.timedelta(1))]

#TODO: This stratey really is just a static portfolio target and a buy and hold trading period
#REFACTOR
class BuyAndHoldStocksAndBonds(Strategy):
    """ Purchases the SPY and LQD at the begining period and holds it to the end """

    def __init__(self, asset_factory, begin_date):
        super(BuyAndHoldStocksAndBonds, self).__init__(portfolio.MixedBuyAndHold(begin_date), asset_factory)
        self.asset_factory = asset_factory
        self.__begin_date = begin_date

    def periods_during(self, begin_date, end_date):
        """ Buy and hold only has one single period """

        yield TradingPeriod(begin_date, end_date)

    def forecast(self, date):
        """ We forecast two assets - stocks and corporate bonds """
        forecaster = weathermen.NullForecaster()
        return [forecaster.forecast(self.asset_factory.make_asset("SPY"), date, datetime.timedelta(1)),
                forecaster.forecast(self.asset_factory.make_asset("LQD"), date, datetime.timedelta(1))]
