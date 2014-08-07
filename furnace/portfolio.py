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

def total_return(begin_portfolio, end_portfolio):
    """ Price return and Dividend return """
    return 1.0 + (end_portfolio.cash_value() - begin_portfolio.cash_value()) / begin_portfolio.cash_value()

# pylint: disable=R0903
#NOTE: too many public methods
class SingleAsset(PortfolioOptimizer):
    """ A portfolio that holds a single asset - gets the asset to hold from its asset universe """

    def optimize(self, _, asset_universe):
        """ We simply hold 100% of whatever asset we are restricted to """
        assert asset_universe.cardinality() == 1
        asset = [symbol for symbol in asset_universe][0]
        return TargetPortfolio([Position(asset, Share(1.0))])
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

#        import IPython
#        IPython.embed()
        return series

    index_value = pandas.concat([make_partial_index(weighting) for weighting in weightings], axis=1).sum(axis=1)
#    index_value = pandas.concat([make_partial_index(weighting) for weighting in weightings], axis=1)
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

class Portfolio(object):
    """ A collection of assets and their share/holdings """
    def __init__(self, positions, date):
        self._positions = positions
        self._date = date

    def make_index(self):
        """ Returns the index equivalent of this portfolio """
        total_basis = self.cash_value()
        weightings = [position.as_weight(total_basis, self.date()) for position in self._positions]
        return make_index(weightings, self.date())

    def cash_value(self):
        """ The cash value of this portfolio """
        return sum([position.cash_value(self._date) for position in self._positions])

    def reinvest_dividends(self, date):
        """ Return a new portfolio adjusted for dividends accrued to date """
        assert date >= self._date
        return Portfolio([p.reinvest_dividends(self._date, date) for p in self._positions], date)

    def date(self):
        """ Getter for the date of this portfolio """
        return self._date

    def rebalance(self, target_portfolio, date):
        """ Rebalances this portfolio to the target's weightings """
        return target_portfolio.create(self.reinvest_dividends(date).cash_value(), date)

class TargetPortfolio(object):
    """ Represents a unit portfolio who's weightings add up to 1 """

    def __init__(self, positions):
        self._positions = positions
        assert Share.proportion([position.share() for position in self._positions]) == 1.0

    def create(self, cash_value, date):
        """ Creates a real portfolio with value to match this target """
        return Portfolio([Position(position.asset(), position.share() * cash_value) for position in self._positions],
                         date)

    def index_portfolio(self, date):
        """ Creates a real portfolio with cash value of 1.0, useful for indexing """
        #NOTE: for now, indexing just starts at a dollar. But eventually we need to take into account comissions and
        #indecies have no way to do something like that, so they'd be comission agnostic. An indexed portfolio may
        #need to be a completely different type that works like a portfolio object but is initialized to a value of 1.0
        #and pays no comissions. It may even have more loose rules regarding bid vs ask.
        return self.create(1.0, date)

class Position(object):
    """ Represents a certain holding of an asset """
    def __init__(self, asset, share):
        self._asset = asset

        assert isinstance(share, Share)
        self._share = share

    def asset(self):
        """ Getter for the asset """
        return self._asset

    def share(self):
        """ Getter for the share """
        return self._share

    def cash_value(self, date):
        """ Returns the cash value of this position """
        return self._share.cash_value(self._asset.price(date))

    def reinvest_dividends(self, begin, end):
        """ Creates a new position with the share adjusted for reinvested dividends between begin
            and end dates """
        dividend_yield = 1.0 + self._asset.yield_between(begin, end)
        return Position(self._asset, self._share * dividend_yield)

    def as_weight(self, total, date):
        """ Creates a weighting representing this position assuming the total portfolio value is total """
        return Weighting(self.asset(), self.cash_value(date) / total)

class Weight(object):
    """ An asset and a % weight it will be held in an index """
    def __init__(self, asset, weight):
        """ Asset is an asset table, weight is a real currently between 0 and
        1.0. Weights higher than 1.0 can be added later to support margin
        accounts, and less than 0.0 to support shorting """
        assert weight <= 1.0
        self._asset = asset
        self._weight = weight

    def price(self, date):
        """ why do you want to know the price? """
        pass


# pylint: disable=R0903
#NOTE: too few public methods
class Share(object):
    """ Represents a holding an asset """
    def __init__(self, share):
        self._share = share

    def __mul__(self, rhs):
        return Share(self._share * rhs)

    def cash_value(self, price):
        """ Returns the cash value of this share given a price """
        return price * self._share

    @staticmethod
# pylint: disable=W0212
# NOTE: not private access as we use a static method on the class itself
    def proportion(shares):
        """ Returns the total proportion that shares represent from 0% to 100% """
        assert all(isinstance(share, Share) for share in shares)
        return sum(share._share for share in shares)
#pylint: enable=R0903,W0212
