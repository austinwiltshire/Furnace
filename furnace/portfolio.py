""" Portfolio tracking and optimization """

import abc

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

def growth(begin_portfolio, end_portfolio):
    """ The growth or reduction in cash value from the begin to the end """
    return 1.0 + (end_portfolio.cash_value() - begin_portfolio.cash_value()) / begin_portfolio.cash_value()

# pylint: disable=R0903
#NOTE: too many public methods
class SingleAsset(PortfolioOptimizer):
    """ A portfolio that holds a single asset - gets the asset to hold from its asset universe """

    def optimize(self, _, asset_universe):
        """ We simply hold 100% of whatever asset we are restricted to """
        assert asset_universe.cardinality() == 1
        symbol = asset_universe.supported_symbols().pop()
        return TargetPortfolio([Position(asset_universe.make_asset(symbol), Share(1.0))])
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


class Portfolio(object):
    """ A collection of assets and their share/holdings """
    def __init__(self, positions, date):
        self._positions = positions
        self._date = date

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
        assert sum(position.share()._share for position in self._positions) == 1

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
        dividends_received = 1.0 + self._asset.yield_between(begin, end)

        #accrue dividends for future growth to smooth unless we actually haven't had time to
        dividends_accrued = (1.0 + self._asset.yield_accrued(end)) if begin != end else 1.0
        return Position(self._asset, self._share * dividends_received * dividends_accrued)


# pylint: disable=R0903
#NOTE: too many public methods
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
        return sum(share._share for share in shares) == 1
#pylint: enable=R0903,W0212
