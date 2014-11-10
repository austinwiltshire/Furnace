""" Tests classes and functions in the portfolio module """


from datetime import datetime
from furnace import portfolio
from furnace.test.helpers import make_default_asset_factory, is_close
from furnace.data import fcalendar
from furnace import weathermen

#TODO: look at renaming these
def test_all_spy_index_total_return():
    """ Tests the total return of an all SPY index between 2003-1-2 and 2012-12-31 is same as yahoo adj return
        for same period """

    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    asset_factory = make_default_asset_factory(["SPY"])
    spy = asset_factory.make_asset("SPY")

    index = portfolio.Weightings([portfolio.Weighting(spy, 1.0)]).make_index_on(begin)
    adj_return = spy.yahoo_adjusted_return(begin, end)

    assert is_close(index.total_return_by(end), adj_return)

def test_all_lqd_index_total_return():
    """ Test that all lqd index has total return equal to yahoo adj close from 2003-1-2 to 2012-12-31 """

    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    asset_factory = make_default_asset_factory(["LQD"])
    lqd = asset_factory.make_asset("LQD")

    index = portfolio.Weightings([portfolio.Weighting(lqd, 1.0)]).make_index_on(begin)
    adj_return = lqd.yahoo_adjusted_return(begin, end)

    assert is_close(index.total_return_by(end), adj_return)

def test_empty_mixed_index():
    """ Tests that an index of multiple assets but logically single is the same as a single asset index """

    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    asset_factory = make_default_asset_factory(["SPY", "LQD"])
    lqd = asset_factory.make_asset("LQD")
    spy = asset_factory.make_asset("SPY")

    index = portfolio.Weightings([portfolio.Weighting(spy, 0.0), portfolio.Weighting(lqd, 1.0)]).make_index_on(begin)
    index2 = portfolio.Weightings([portfolio.Weighting(lqd, 1.0)]).make_index_on(begin)

    assert is_close(index.total_return_by(end), index2.total_return_by(end))

def test_spy_lqd_mix_index_ttl_rtn():
    """ Test an index of 50% spy and 50% lqd, total_return_by, between 2003-1-2 and 2012-12-31
     hand calculated on aug 20th with yahoo adj close """

    #NOTE: Adjusted close floats with time, meaning with different data adjusted close changes even on the same
    #dates. This does not always seem geometrically stable as long term returns can shift even though they've
    #'already' happened. This is one benefit of using one stable understood system than relying on yahoo's black
    #magic adjusted close.

    asset_factory = make_default_asset_factory(["SPY", "LQD"])

    index = portfolio.Weightings([portfolio.Weighting(asset_factory.make_asset("LQD"), 0.5),
                                  portfolio.Weighting(asset_factory.make_asset("SPY"), 0.5)]).make_index_on(
                                 datetime(2003, 1, 2))

    assert is_close(index.total_return_by(datetime(2012, 12, 31)), .900)

def test_proportional_weighting():
    """ Test the proportional weighting portfolio optimization strategy. Weights based on forecasts' idea of simple
    sharpe proportionally """
    asset_factory = make_default_asset_factory(["SPY", "LQD"])

    portfolio_opt = portfolio.ProportionalWeighting(["SPY", "LQD"])
    weightings = portfolio_opt.optimize(weathermen.HistoricalAverageForecast(asset_factory), asset_factory)

    spy = asset_factory.make_asset("SPY")
    lqd = asset_factory.make_asset("LQD")

    #these weightings were hand calculated on october 29
    optimal_weightings = portfolio.Weightings([portfolio.Weighting(spy, .302), portfolio.Weighting(lqd, .698)])

    assert optimal_weightings == weightings
