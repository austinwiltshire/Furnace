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
        return Portfolio([Position(forecasts[0].asset(), Share(1.0))], date)

class MixedBuyAndHold(PortfolioOptimizer):
    """ Purchases 80% SPY and 20% BIL """
    def __init__(self, begin_date):
        super(MixedBuyAndHold, self).__init__()
        self._begin_date = begin_date
        #TODO: could take in the asset names i want to track and then look them up in the forecasts

    def optimize(self, forecasts, date):
        return Portfolio([Position(forecasts[0].asset(), Share(.1)), Position(forecasts[1].asset(), Share(.9))], date)

class Portfolio:
    """ A collection of assets and their share/holdings """
    def __init__(self, positions, date):
        self._positions = positions
        self._date = date

    def value(self):
        """ Returns the share of this portfolio times the price of the assets, roughly how much money you'd need for
            'one share' of this portfolio """
        #TODO: rename "index value" since it's not a true value as we don't really own mroe than 'one unit' over time
        return sum([position.share().value(position.asset().price(self._date)) for position in self._positions])

    def yield_(self):
        """ The CAGR of this portfolio's interest and dividend payments """
        pass

    def on_date(self, date):
        """ Returns a new portfolio who's positions are the same but the date is adjusted """
        assert date >= self._date
#        foo = True
        foo = False
        if foo:
            return Portfolio(self._positions, date)
        else:
            return Portfolio([p.reinvest_dividends(self._date, date) for p in self._positions], date).dividends_accrued()

    def date(self):
        """ Getter for the date of this portfolio """
        return self._date

    def dividends_accrued(self):
        """ Creates a new portfolio with next dividend accrued, or partially counted. Used to judge growth - should nto """
        return self

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
        dividends_accrued = 1.0 + self._asset.yield_accrued(end) if begin != end else 1.0
        return Position(self._asset, self._share * dividends_received * dividends_accrued)
    #(1.0 + self._asset.yield_between(begin, end)))

class Share(object):
    """ Represents a holding an asset """
    def __init__(self, share):
        self._share = share

    def __mul__(self, rhs):
        return Share(self._share * rhs)

    def value(self, price):
        """ Returns the value of this share given a price """
        return price * self._share
