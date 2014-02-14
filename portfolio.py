""" Portfolio tracking and optimization """

class PortfolioOptimizer(object):
    """ Given a forecast for a set of assets, returns the optimal weighting of each asset in a
    portfolio """
    def __init__(self):
        pass

    def optimize(self, forecasts, date):
        """ Forecasts need to be able to back point to their asset class and thus implicitly define
        the asset universe """
        raise Exception("Not implemented yet")

def growth(begin_portfolio, end_portfolio):
    """ The growth or reduction in value from the begin to the end """
    return 1.0 + (end_portfolio.value() - begin_portfolio.value()) / begin_portfolio.value()

class BuyAndHoldPortfolio(PortfolioOptimizer):
    """ Purchases the SPY at the begining period and holds it to the end """
    def __init__(self, begin_date):
        super(BuyAndHoldPortfolio, self).__init__()
        self._begin_date = begin_date

    def optimize(self, forecasts, date):
        """ Simply sets 100% weight to the first asset returned in the forecast """
        return Portfolio([Position(forecasts[0].asset(), Weight(1.0))], date)

class Portfolio:
    """ A collection of assets and their weights/holdings """
    def __init__(self, positions, date):
        #TODO: assert that weights add up to 100%
        self._positions = positions
        self._date = date

    def value(self):
        """ What's the value of this portfolio? """
        #TODO: come up with better name, this isn't really the 'value'
        """ Returns the weights of this portfolio times the price of the assets, roughly how much money you'd need for 'one share' of this portfolio """
        return sum([position.weight() * position.asset().price(self._date) for position in self._positions])

    def date(self):
        """ Getter for the date of this portfolio """
        return self._date

class Position(object):
    """ Represents a certain holding of an asset """
    def __init__(self, asset, weight):
        self._asset = asset
        self._weight = weight

    def asset(self):
        """ Getter for the asset """
        return self._asset

    def weight(self):
        """ Getter for the weight """
        return self._weight

class Weight(object):
    """ Represents a weighting out of 100% of holding an asset """
    def __init__(self, weight):
        self._weight = weight

    def __mul__(self, rhs):
        return self._weight * rhs
