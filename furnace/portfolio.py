""" Portfolio tracking and optimization """

import abc

# pylint: disable=R0903
#NOTE: too few public methods
class PortfolioOptimizer(object):
    """ Given a forecast for a set of assets, returns the optimal weighting of each asset in a
    portfolio """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def optimize(self, forecasts):
        """ Forecasts need to be able to back point to their asset class and thus implicitly define
        the asset universe """
        pass
#pylint: enable=R0903

def growth(begin_portfolio, end_portfolio):
    """ The growth or reduction in value from the begin to the end """
    return 1.0 + (end_portfolio.value() - begin_portfolio.value()) / begin_portfolio.value()

#TODO: buy and hold is really a rebalancing rule - i.e., the trading period is from complete beginning to end.
#100% stocks and 80% stocks and 20% bonds are both examples of a static portfolio with a buy and hold horizon
# pylint: disable=R0903
#NOTE: too many public methods
class BuyAndHoldPortfolio(PortfolioOptimizer):
    """ Purchases the SPY at the begining period and holds it to the end """
    def __init__(self, begin_date):
        super(BuyAndHoldPortfolio, self).__init__()
        self._begin_date = begin_date

    def optimize(self, forecasts):
        """ Simply sets 100% weight to the first asset returned in the forecast """
        return TargetPortfolio([Position(forecasts[0].asset(), Share(1.0))])
#pylint: enable=R0903

#TODO: this is really just a 'static strategy' for portfolios. It can be changed orthogonal to a rebalancing rule
#and can have hard percentage targets to rebalance the value of the portfolio to.
# pylint: disable=R0903
#NOTE: too many public methods
class MixedBuyAndHold(PortfolioOptimizer):
    """ Purchases 80% SPY and 20% BIL """
    def __init__(self, begin_date):
        super(MixedBuyAndHold, self).__init__()
        self._begin_date = begin_date
        #TODO: could take in the asset names i want to track and then look them up in the forecasts

    def optimize(self, forecasts):
        return TargetPortfolio([Position(forecasts[0].asset(), Share(.8)), Position(forecasts[1].asset(), Share(.2))])
#pylint: enable=R0903

class Portfolio(object):
    """ A collection of assets and their share/holdings """
    def __init__(self, positions, date):
        self._positions = positions
        self._date = date

    def value(self):
        """ Returns the share of this portfolio times the price of the assets, roughly how much money you'd need for
            'one share' of this portfolio """
        #TODO: analyze code base for use of indexes versus values. portfolios have values, but can be used
        #as indecies
        return sum([position.share().value(position.asset().price(self._date)) for position in self._positions])

    def on_date(self, date):
        """ Returns a new portfolio who's positions are the same but the date is adjusted """
        assert date >= self._date
        return Portfolio([p.reinvest_dividends(self._date, date) for p in self._positions], date)

    def date(self):
        """ Getter for the date of this portfolio """
        return self._date

    def rebalance(self, target_portfolio, date):
        """ Rebalances this portfolio to the target's weightings """
        return target_portfolio.create(self.on_date(date).value(), date)

class TargetPortfolio(object):
    """ Represents a unit portfolio who's weightings add up to 1 """

    def __init__(self, positions):
        self._positions = positions
        assert sum(position.share()._share for position in self._positions) == 1

    def create(self, value, date):
        """ Creates a real portfolio with value to match this target """
        return Portfolio([Position(position.asset(), position.share() * value) for position in self._positions], date)

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

    def value(self, price):
        """ Returns the value of this share given a price """
        return price * self._share
#pylint: enable=R0903
