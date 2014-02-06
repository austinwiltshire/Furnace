import datetime
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


# Ultimately the metrics forecasted as inputs for the optimizer are part of the financial strategy and may have different models for each one

class Weatherman:
    def forecast(self, asset, time_point, period):
        raise Exception("Not implemented yet")

#A simple guess forecaster, probably should stick to the Macy's Thanksgiving days parade
class AlRoker(Weatherman):
    def forecast(self, asset, time_point, period):
        return SimpleReturn(.01) #sounds about right?

#Represents projected metrics from a forecaster
class Forecast:
    pass

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

        metrics = []

        for trading_period in strategy.periods_during(datetime.date(2001,1,1), datetime.date(2013,1,1)):
            #  a trading period needs to be a pair of dates so we can calculate return during the whole time. the simplest trading period would have
            # an ending date the same as the next period's begin date

            # the portfolios need to know their dates for metrics to be useful
            begin_portfolio = strategy.portfolio_on(trading_period.begin())
            end_portfolio = strategy.portfolio_on(trading_period.end())

            metrics.append(self.generate_metrics(begin_portfolio, end_portfolio))


        #we want to pass a set of trading periods in with their inputs as we'd know them
        #and get the portfolio the strategy would hold back out
        #then we'd need to calculat the actual return for that portfolio
        #once we have the actual returns for the entire portfolio we can calculate metrics like:
        # - equity curve
        # - cagr
        # - volatility
        # - max drawdown

        return metrics

    def generate_metrics(self, begin_portfolio, end_portfolio):
        """ Right now just generates growth for CAGR """
        return growth(begin_portfolio, end_portfolio)

def growth(begin_portfolio, end_portfolio):
    """ The growth or reduction in value from the begin to the end """
    #TODO: better
    return 1.0

class Strategy:
    """ A pair of weatherman and portfolio optimizer """
    pass

class SimpleStrategy(Strategy):
    """ Al Roker and a first year business student walk into a bar... """
    def portfolio_optimizer(self):
        return FreshmanBusinessStudent()

    def weatherman(self):
        return AlRoker()

    def periods_during(self, begin_date, end_date):
        """ Simple strategy simply trades daily """

        #TODO: pick better dates obviously
        for day in range((end_date - begin_date).days):
            yield TradingPeriod(begin_date, begin_date + datetime.timedelta(day))

    def portfolio_on(self, date):
        """ Generates a portfolio this strategy would recommend for date """

        #TODO: generate a better portfolio
        return Portfolio([Position(Asset("SPY"),Weight(1.0))])

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
        pass

class Asset:
    """ Represents a tradable security, by symbol """
    def __init__(self, symbol):
        pass

class Weight:
    """ Represents a weighting out of 100% of holding an asset """
    def __init__(self, weight):
        pass

class Portfolio:
    """ A collection of assets and their weights/holdings """
    def __init__(self, positions):
        pass

class PerformanceMetrics:
    """ Currently just CAGR """
    pass

def main():
    f = Furnace()
    p = f.fire(SimpleStrategy())
    print p


if "__main__"==__name__:
    main()
