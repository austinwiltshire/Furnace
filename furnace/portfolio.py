""" Portfolio tracking and optimization """

import abc
import pandas
import numpy
import portfolio

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
#NOTE: too many public methods
class SingleAsset(PortfolioOptimizer):
    """ A portfolio that holds a single asset - gets the asset to hold from its asset universe """

    def optimize(self, _, asset_universe):
        """ We simply hold 100% of whatever asset we are restricted to """
        assert asset_universe.cardinality() == 1
        asset = [symbol for symbol in asset_universe][0]
        return portfolio.Weightings([portfolio.Weighting(asset, 1.0)])
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

class Weightings(object):
    """ Represents multiple asset weights that add up to 1.0 """
    def __init__(self, weightings):
        """ Takes in a list of Weighting objects """
        assert numpy.isclose(sum(weighting.weight() for weighting in weightings), 1.0)
        self._weightings = weightings

    def __iter__(self):
        """ Iterate over the weights """
        return iter(self._weightings)

    def make_index_on(self, date):
        return make_index(self, date)


class Weighting(object):
    def __init__(self, asset, weight):
        self._asset = asset
        self._weight = weight

    def asset(self):
        return self._asset

    def weight(self):
        return self._weight

def make_index(weightings, date):
    """ Returns an index object from a list of weightings. Weightings must add
    up to 1.0 """
    assert numpy.isclose(sum(weighting.weight() for weighting in weightings), 1.0)

    #computes the decomposed total return of a weighted asset
    #TODO: add a regression test around this - should have same return as adjusted close of spy for same period
    def make_partial_index(weighting):
        """ Helper method adds necessary columns to a table """
        table = weighting.asset().table()[['Close', 'Dividends']]
        table = table[table.index >= date]

        accumulated_yields = ((table['Dividends'] / table['Close']) + 1.0).dropna().cumprod()
        initial_basis = weighting.weight() / table.ix[date]['Close']

        #NOTE: we assume dividends are reinvested on the day of
        adjusted_basis = accumulated_yields.reindex(table.index, method='ffill', fill_value=1.0) * initial_basis

        series = table['Close'] * adjusted_basis
        series.name = weighting.asset().symbol() + "_partial_adjusted_value"

        return series

    index_value = pandas.concat([make_partial_index(weighting) for weighting in weightings], axis=1).sum(axis=1)
    return Index(index_value, weightings, date)

class Index(object):
    """ A collection of assets held by weighting indexed to 1.0 on date """

    def __init__(self, table, weightings, date):
        self.table = table
        self._weightings = weightings
        self._date = date

    def total_return_by(self, date):
        """ Calculates total return by a certain date """
        assert date >= self._date

        return self.table[date] - 1.0

