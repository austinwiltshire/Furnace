import datetime
import csv
import scipy.stats.mstats
import numpy
# Initial prototype
# Needs to make a mock strategy 
# - A mock forecast (forecaster module called weatherman?)
# - A mock portfolio optimizer
# Initial testing framework that loads in asset class information
# Runs initial test

# The portfolio optimizer knows what the metrics it needs to optimize are, and those metrics
# Ultimately are the output variables of what the forecast needs to generate. So in terms of 
# strategy, the portfolio optimizer shoudl be feeding in to the weatherman what he needs to be
# predicting. 

#Given a time point, returns a forecast of key metrics for an asset class
#over a corresponding period
#First metrics will be expected return, expected volatility and expected correlation

#Steps:
# - Implement a buy and hold on the spy strategy
# - Implement an 80%/20% strategy of spy and lqd

# Ultimately the metrics forecasted as inputs for the optimizer are part of the financial strategy and may have different models for each one

def make_line(line):
    #TODO: probably put into data frame format
    return {"Date":datetime.datetime.strptime(line[0], "%Y-%m-%d").date(), "Open":float(line[1]), "High":float(line[2]), "Low":float(line[3]), "Close":float(line[4]), "Volume":int(line[5])}

def load():
    return dict([(l["Date"], l) for l in [make_line(line) for line in [l for l in csv.reader(open("spy.csv"))][1:]]])

class Weatherman:
    def forecast(self, asset, time_point, period):
        raise Exception("Not implemented yet")

#A simple guess forecaster, probably should stick to the Macy's Thanksgiving days parade
class AlRoker(Weatherman):
    def forecast(self, asset, time_point, period):
        return SimpleReturn(.01) #sounds about right?

class Forecast:
    """ Represents metrics from a forecaster. Currently assumes growth but can be attached to any value in the future """
    def __init__(self, asset, growth):
        self._asset = asset
        self._growth = growth

    def asset(self):
        return self._asset

    def growth(self):
        return self._growth

class SimpleReturn(Forecast):
    "A forecast of the return of an asset class"
    def __init__(self, return_, asset_class):
        self.return_ = return_

class PortfolioOptimizer:
    """ Given a forecast for a set of assets, returns the optimal weighting of each asset in a 
    portfolio """
    def optimize(self, forecasts):
        """ Forecasts need to be able to back point to their asset class and thus implicitly define
        the asset universe """
        raise Exception("Not implemented yet")

class FreshmanBusinessStudent(PortfolioOptimizer):
    """ A really dumb portfolio optimizer. Simply returns 100% on the first asset in the list """
    def optimizer(self, forecasts):
        return Portfolio(Weight(100, forecasts[0].asset_class))

class Furnace:
    """ Our testing framework """
    def fire(self, strategy):
        """ Given a financial strategy, returns performance metrics for it """
        #the testing framework should just pass in, say, date ranges and it'd then remain period agnostic
        #once we have the date ranges, we can then ask the trading strategy what its periods would be, and generate the trading periods
        #we ultimately want - for a particular date (dates set by the periodicity), what are the holdings the strategy would advise
        #then what are the returns of those holdings over the period?

        performance_measurements = []

        for trading_period in strategy.periods_during(datetime.date(2001,1,2), datetime.date(2012,12,31)):
            #  a trading period needs to be a pair of dates so we can calculate return during the whole time. the simplest trading period would have
            # an ending date the same as the next period's begin date

            # the portfolios need to know their dates for metrics to be useful
            begin_portfolio = strategy.portfolio_on(trading_period.begin())
            end_portfolio = strategy.portfolio_on(trading_period.end())

            performance_measurements.append(self.measure_performance(begin_portfolio, end_portfolio))


        #we want to pass a set of trading periods in with their inputs as we'd know them
        #and get the portfolio the strategy would hold back out
        #then we'd need to calculat the actual return for that portfolio
        #once we have the actual returns for the entire portfolio we can calculate metrics like:
        # - equity curve
        # - cagr
        # - volatility
        # - max drawdown

        return self.generate_metrics(performance_measurements)

    def generate_metrics(self, performance_measurements):
        """ Calculates CAGR """
        return scipy.stats.mstats.gmean(performance_measurements)
        
    def measure_performance(self, begin_portfolio, end_portfolio):
        """ Right now just generates growth for CAGR """
        return growth(begin_portfolio, end_portfolio)

def growth(begin_portfolio, end_portfolio):
    """ The growth or reduction in value from the begin to the end """
    return 1.0 + (end_portfolio.value() - begin_portfolio.value()) / begin_portfolio.value()

class Strategy:
    """ A pair of weatherman and portfolio optimizer """
    pass


class BuyAndHoldPortfolio(PortfolioOptimizer):
    """ Purchases the SPY at the begining period and holds it to the end """
    def __init__(self, begin_date):
        self._begin_date = begin_date

    def optimize(self, forecasts, date):
        return Portfolio([Position(forecasts[0].asset(), Weight(1.0))], date)

class NullForecaster(Weatherman):
    """ Returns no change for all assets """
    def forecast(self, asset, time_point, period):
        return Forecast(asset, 1.0)

class BuyAndHoldStocks(Strategy):
    """ Purchases the SPY at the begining period and holds it to the end """

    def __init__(self, assetFactory, begin_date):
        self._assetFactory = assetFactory
        self._begin_date = begin_date
        self._forecaster = self.weatherman()
        self._portfolio_optimizer = self.portfolio_optimizer()

    def portfolio_optimizer(self):
        return BuyAndHoldPortfolio(self._begin_date)

    def weatherman(self):
        return NullForecaster()

    def periods_during(self, begin_date, end_date):
        """ Simple strategy simply trades daily """

        #TODO: pick better dates obviously
        for day in range((end_date - begin_date).days):
            yield TradingPeriod(begin_date + datetime.timedelta(day), begin_date + datetime.timedelta(day + 1))

    def portfolio_on(self, date):
        """ Generates a portfolio this strategy would recommend for date """

        forecast = [self._forecaster.forecast(self._assetFactory.make_asset("SPY"), date, datetime.timedelta(1))]
        portfolio = self._portfolio_optimizer.optimize(forecast, date)
        return portfolio


class AssetFactory:
    def __init__(self, data_cache):
        self._data_cache = data_cache

    def make_asset(self, symbol):
        return Asset(symbol, self._data_cache)

class TradingPeriod:
    """ The begining and end of an entire trading period on which metrics can be collected """
    def __init__(self, begin, end):
        self._begin = begin
        self._end = end

    def begin(self):
        return self._begin

    def end(self):
        return self._end

class Position:
    """ Represents a certain holding of an asset """
    def __init__(self, asset, weight):
        self._asset = asset
        self._weight = weight

    def asset(self):
        return self._asset

    def weight(self):
        return self._weight

class Asset:
    """ Represents a tradable security, by symbol """
    def __init__(self, symbol, data_cache):
        self._symbol = symbol
        self._data_cache = data_cache

    def price(self, date):
        #TODO: this is a little too OO given that we're going to be dealing with big rows of things, so we may end up doing a big query at the front and then looking up things in a cache
        #TODO: do a price lookup in our data warehouse
        #TODO: handle missing dates better:

        try:
            return self._data_cache[self._symbol][date]["Close"]
        except(KeyError):
            return self.price(date - datetime.timedelta(1))

class Weight:
    """ Represents a weighting out of 100% of holding an asset """
    def __init__(self, weight):
        self._weight = weight

    def __mul__(self, rhs):
        return self._weight * rhs

class Portfolio:
    """ A collection of assets and their weights/holdings """
    def __init__(self, positions, date):
        #TODO: assert that weights add up to 100%
        self._positions = positions
        self._date = date

    def value(self):
        #TODO: come up with better name, this isn't really the 'value'
        """ Returns the weights of this portfolio times the price of the assets, roughly how much money you'd need for 'one share' of this portfolio """
        return sum([position.weight() * position.asset().price(self._date) for position in self._positions]) 

    def date(self):
        return self._date

class PerformanceMetrics:
    """ Currently just CAGR """
    pass

def main():
    f = Furnace()
    data_cache = {}
    data_cache["SPY"] = load()
    p = f.fire(BuyAndHoldStocks(AssetFactory(data_cache),datetime.date(2001,1,2)))
    assert numpy.isclose(p, 1.00002291096, 1e-12, 1e-12)
    print p

if "__main__"==__name__:
    main()
