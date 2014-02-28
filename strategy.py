""" For overall financial strategies - pairs of forecasters and portfolio optimizers """

# Ultimately the metrics forecasted as inputs for the optimizer are part of the financial strategy and may have different models for each one

import performance
import weathermen
import portfolio
import datetime

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
    def __init__(self):
        pass

class BuyAndHoldStocks(Strategy):
    """ Purchases the SPY at the begining period and holds it to the end """

    def __init__(self, assetFactory, begin_date):
        super(BuyAndHoldStocks, self).__init__()
        self.assetFactory = assetFactory
        self.__begin_date = begin_date
        self.__forecaster = self.weatherman()
        self.__portfolio_optimizer = self.portfolio_optimizer()

    def portfolio_optimizer(self):
        """ Uses a simple buy and hold """
        return portfolio.BuyAndHoldPortfolio(self.__begin_date)

    def weatherman(self):
        """ Uses a null forecast """
        return weathermen.NullForecaster()

    def periods_during(self, begin_date, end_date):
        """ Buy and hold only has one single period """

        yield TradingPeriod(begin_date, end_date)

    def portfolio_on(self, date):
        """ Generates a portfolio this strategy would recommend for date """

        forecast = [self.__forecaster.forecast(self.assetFactory.make_asset("SPY"), date, datetime.timedelta(1))]
        portfolio_ = self.__portfolio_optimizer.optimize(forecast, date)
        return portfolio_

    def performance_during(self, begin_date, end_date):
        """ Gets the overall performance from begin_date to end_date """
        period_performances = []
        for trading_period in self.periods_during(begin_date, end_date):
            beginning_portfolio = self.portfolio_on(trading_period.begin())
#            performances.append(performance.PeriodPerformance(beginning_portfolio, beginning_portfolio.on_date(trading_period.end())))
            period_performances.append(performance.PeriodPerformance(beginning_portfolio, self.portfolio_on(trading_period.end())))
        return performance.OverallPerformance(period_performances)

class BuyAndHoldStocksAndBonds(Strategy):
    """ Purchases the SPY and LQD at the begining period and holds it to the end """

    def __init__(self, asset_factory, begin_date):
        super(BuyAndHoldStocksAndBonds, self).__init__()
        self.asset_factory = asset_factory
        self.__begin_date = begin_date
        self.__forecaster = self.weatherman()
        self.__portfolio_optimizer = self.portfolio_optimizer()

    def portfolio_optimizer(self):
        """ Uses a simple buy and hold """
        return portfolio.MixedBuyAndHold(self.__begin_date)

    def weatherman(self):
        """ Uses a null forecast """
        return weathermen.NullForecaster()

    def periods_during(self, begin_date, end_date):
        """ Buy and hold only has one single period """

        yield TradingPeriod(begin_date, end_date)

    def portfolio_on(self, date):
        """ Generates a portfolio this strategy would recommend for date """

        forecast = [self.__forecaster.forecast(self.asset_factory.make_asset("SPY"), date, datetime.timedelta(1)),
                    self.__forecaster.forecast(self.asset_factory.make_asset("LQD"), date, datetime.timedelta(1))]
        portfolio_ = self.__portfolio_optimizer.optimize(forecast, date)
        return portfolio_

    def performance_during(self, begin_date, end_date):
        """ Gets the overall performance from begin_date to end_date """
        return performance.OverallPerformance([performance.PeriodPerformance(self.portfolio_on(trading_period.begin()), self.portfolio_on(trading_period.end())) for trading_period in self.periods_during(begin_date, end_date)])


#TODO: need to refactor out commonality above, possibly dependency injecting into the Strategy things like - weatherman, portfolio optimizer and trading period as well as performance during
