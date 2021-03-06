""" Tests classes and functions in the portfolio module """

from datetime import datetime
from furnace import portfolio
from furnace.test.helpers import is_close, DEFAULT_ASSET_FACTORY
from furnace import weathermen

def test_index_total_return_spy():
    """ Tests the total return of an all SPY index between 2003-1-2 and 2012-12-31 is same as yahoo adj return
        for same period """

    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    spy = DEFAULT_ASSET_FACTORY.make_asset("SPY")

    index = portfolio.Weightings([portfolio.Weighting(spy, 1.0)]).make_index_on(begin, end)
    adj_return = spy.yahoo_adjusted_return(begin, end)

    assert is_close(index.total_return_by(end), adj_return)

#TODO: make this a test on the lqd asset and reduce tests on index_on to just one, but pick an asset that has both
#dividends and splits
def test_index_total_return_lqd():
    """ Test that all lqd index has total return equal to yahoo adj close from 2003-1-2 to 2012-12-31 """

    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    lqd = DEFAULT_ASSET_FACTORY.make_asset("LQD")

    index = portfolio.Weightings([portfolio.Weighting(lqd, 1.0)]).make_index_on(begin, end)
    adj_return = lqd.yahoo_adjusted_return(begin, end)

    assert is_close(index.total_return_by(end), adj_return)

def test_empty_mixed_index():
    """ Tests that an index of multiple assets but logically single is the same as a single asset index """

    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    lqd = DEFAULT_ASSET_FACTORY.make_asset("LQD")
    spy = DEFAULT_ASSET_FACTORY.make_asset("SPY")

    weighting = portfolio.Weighting
    index = portfolio.Weightings([weighting(spy, 0.0), weighting(lqd, 1.0)]).make_index_on(begin, end)
    index2 = portfolio.Weightings([weighting(lqd, 1.0)]).make_index_on(begin, end)

    assert is_close(index.total_return_by(end), index2.total_return_by(end))

def test_split_mixed_index():
    """ Test an index of 50% spy and 50% lqd, total_return_by, between 2003-1-2 and 2012-12-31
     hand calculated on aug 20th with yahoo adj close """

    #NOTE: Adjusted close floats with time, meaning with different data adjusted close changes even on the same
    #dates. This does not always seem geometrically stable as long term returns can shift even though they've
    #'already' happened. This is one benefit of using one stable understood system than relying on yahoo's black
    #magic adjusted close.

    weighting = portfolio.Weighting
    index = portfolio.Weightings([
        weighting(DEFAULT_ASSET_FACTORY.make_asset("LQD"), 0.5),
        weighting(DEFAULT_ASSET_FACTORY.make_asset("SPY"), 0.5)
    ]).make_index_on(
        datetime(2003, 1, 2),
        datetime(2012, 12, 31)
    )

    assert is_close(index.total_return_by(datetime(2012, 12, 31)), .900)

def test_proportional_weighting():
    """ Test the proportional weighting portfolio optimization strategy. Weights based on forecasts' idea of simple
    sharpe proportionally """

    universe = DEFAULT_ASSET_FACTORY.make_universe(["SPY", "LQD"])

    portfolio_opt = portfolio.ProportionalWeighting(universe)
    weightings = portfolio_opt.optimize(
            weathermen.HistoricalAverage(DEFAULT_ASSET_FACTORY), DEFAULT_ASSET_FACTORY
    )

    spy = DEFAULT_ASSET_FACTORY.make_asset("SPY")
    lqd = DEFAULT_ASSET_FACTORY.make_asset("LQD")

    #these weightings were hand calculated on october 29
    optimal_weightings = portfolio.Weightings([portfolio.Weighting(spy, .302), portfolio.Weighting(lqd, .698)])

    assert optimal_weightings == weightings
