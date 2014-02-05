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
        raise Exception("Not implemented yet")

class Strategy:
    """ A pair of weatherman and portfolio optimizer """
    pass

class SimpleStrategy(Strategy):
    """ Al Roker and a first year business student walk into a bar... """
    def portfolio_optimizer(self):
        return FreshmanBusinessStudent()

    def weatherman(self):
        return AlRoker()

class PerformanceMetrics:
    """ Currently just CAGR """
    pass

def main():
    f = Furnace()
    p = f.fire(SimpleStrategy())
    print p


if "__main__"==__name__():
    main()
