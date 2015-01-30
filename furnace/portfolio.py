""" Portfolio tracking and optimization """

import abc
import pandas
import numpy

# pylint: disable=R0903
#NOTE: too few public methods
class PortfolioOptimizer(object):
    """ Given a forecast for a set of assets, returns the optimal weighting of each asset in a
    portfolio """
    __metaclass__ = abc.ABCMeta

#NOTE: do not add asset universe as an init param - strategy ensures that the same asset universe is passed in to
#portfolio optimizer and weatherman
    @abc.abstractmethod
    def optimize(self, forecasts, asset_universe):
        """ Forecasts need to be able to back point to their asset class and thus implicitly define
        the asset universe """
        pass
#pylint: enable=R0903

# pylint: disable=R0903
#NOTE: too few public methods
class SingleAsset(PortfolioOptimizer):
    """ A portfolio that holds a single asset - gets the asset to hold from its asset universe """
    def __init__(self, asset):
        self._asset = asset

    def optimize(self, _, asset_universe):
        """ We hold 100% of one asset """
#        assert asset_universe.cardinality() == 1
#        asset = [symbol for symbol in asset_universe.symbols()][0]
        return Weightings([Weighting(self._asset, 1.0)])
#pylint: enable=R0903

# pylint: disable=R0903
#NOTE: too few public methods, assumed will grow as portfolio optimizer grows
class StaticTarget(PortfolioOptimizer):
    """ Optimizes a portfolio towards a statically provided target """
    def __init__(self, target):
        self._target = target

    def optimize(self, _, asset_universe):
        """ We flat out ignore the forecaster argument """
        return self._target
#pylint: enable=R0903

class ProportionalWeighting(PortfolioOptimizer):
    """ Optimizes portfolio by assigning proportionally larger weights to members that offer greater simple sharpe
    ratios based on total asset history
    
    This portfolio does not support short positions and simply exits any potential negative sharpe ratio 
    positions. If all forecasts are negative, it holds an equal weight portfolio """
    def __init__(self, symbols):
        self._symbols = symbols
        self._assets = None
        self._num_assets = len(symbols)

    #TODO: this function is very slow. unsure what to do to speed it up.
    #TODO: clean up the caching of assets, have symbols passed in as assets
    def optimize(self, forecast, asset_universe):
        """ Ignore forecaster for now. """
        if(not self._assets):
            self._assets = [asset_universe.make_asset(symbol) for symbol in self._symbols]

        sharpes = numpy.array([max(forecast.simple_sharpe(asset), 0.0) for asset in self._assets])

        #NOTE: we fallback to an equal weight proportion in the case that all sharpe ratios are negative
        weights = sharpes / sharpes.sum() if sharpes.sum() > 0.0 else numpy.ones(self._num_assets) / self._num_assets
        return Weightings([Weighting(asset, weight) for asset, weight in zip(self._assets, weights)])

class AntiProportionalWeighting(PortfolioOptimizer):
    """ A stand in for basically shorting all the forecasts I'm given """
    def __init__(self, symbols):
        self._symbols = symbols

    def optimize(self, forecast, asset_universe):
        assets = [asset_universe.make_asset(symbol) for symbol in self._symbols]
        sharpes = numpy.array([max(forecast.simple_sharpe(asset), 0.0) for asset in assets])

        #NOTE: we fallback to an equal weight proportion in the case that all sharpe ratios are negative
        weights = sharpes / sharpes.sum() if sharpes.sum() > 0.0 else numpy.ones(len(assets)) / len(assets)
        return Weightings([Weighting(asset, (1.0 - weight) / (len(assets) - 1)) for asset, weight in zip(assets, weights)])

# pylint: disable=R0903
class Weightings(object):
    """ Represents multiple asset weights that add up to 1.0 """
    def __init__(self, weightings):
        """ Takes in a list of Weighting objects """
        assert numpy.isclose(sum(weighting.weight() for weighting in weightings), 1.0)
        self._weightings = weightings

    def __iter__(self):
        """ Iterate over the weights """
        return iter(self._weightings)

    def __eq__(self, other):
        """ Checks for equality """
        zipped_weights = zip(self._weightings, other._weightings) #pylint: disable=W0212
        return all(weight1 == weight2 for weight1, weight2 in zipped_weights)

    def __repr__(self):
        return str(self._weightings)

    def make_index_on(self, begin_date, end_date):
        """ Creates an index of these weightings on date """

        index_value = pandas.concat([weighting.make_partial_index(begin_date, end_date) for weighting in self._weightings], axis=1).sum(axis=1)
        return Index(index_value, self, begin_date)
# pylint: enable=R0903

class Weighting(object):
    """ Represents a weight of an asset in a broader weighting scheme.
    Could potentially support negative (short) and margin weights """
    def __init__(self, asset, weight):
        self._asset = asset
        self._weight = weight

#TODO: remove getter
    def asset(self):
        """ Getter for asset """
        return self._asset

#TODO: remove getter
    def weight(self):
        """ Getter for weight """
        return self._weight

    #computes the decomposed total return of a weighted asset
    def make_partial_index(self, begin_date, end_date=None):
        """ Creates an index who's basis is weighted initially """
        return self.asset().make_index(begin_date, self.weight(), end_date)

    def __eq__(self, other):
        return numpy.isclose(self.weight(), other.weight(), 3) and self.asset() == other.asset()

    def __repr__(self):
        return "<Weighting: " + str(self.asset()) + " at " + str(self.weight()) + "%>"

# pylint: disable=R0903
#NOTE: too few public methods
class Index(object):
    """ A collection of assets held by weighting indexed to 1.0 on date """

    def __init__(self, table, weightings, begin_date):
        self.table = table
        self._weightings = weightings
        self._begin_date = begin_date

    def total_return_by(self, date):
        """ Calculates total return by a certain date """
        assert date >= self._begin_date

        return self.table[date] - 1.0
# pylint: enable=R0903

