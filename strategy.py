import performance
import weathermen
import portfolio
import datetime

class TradingPeriod:
    """ The begining and end of an entire trading period on which metrics can be collected """
    def __init__(self, begin, end):
        self._begin = begin
        self._end = end

    def begin(self):
        return self._begin

    def end(self):
        return self._end

class Strategy:
    """ A pair of weatherman and portfolio optimizer """
    pass

class BuyAndHoldStocks(Strategy):
    """ Purchases the SPY at the begining period and holds it to the end """

    def __init__(self, assetFactory, begin_date):
        self._assetFactory = assetFactory
        self._begin_date = begin_date
        self._forecaster = self.weatherman()
        self._portfolio_optimizer = self.portfolio_optimizer()

    def portfolio_optimizer(self):
        return portfolio.BuyAndHoldPortfolio(self._begin_date)

    def weatherman(self):
        return weathermen.NullForecaster()

    def periods_during(self, begin_date, end_date):
        """ Buy and hold only has one single period """

        yield TradingPeriod(begin_date, end_date)

    def portfolio_on(self, date):
        """ Generates a portfolio this strategy would recommend for date """

        forecast = [self._forecaster.forecast(self._assetFactory.make_asset("SPY"), date, datetime.timedelta(1))]
        portfolio = self._portfolio_optimizer.optimize(forecast, date)
        return portfolio

    def performance_during(self, begin_date, end_date):
        return performance.OverallPerformance([performance.PeriodPerformance(self.portfolio_on(trading_period.begin()), self.portfolio_on(trading_period.end())) for trading_period in self.periods_during(begin_date, end_date)])


