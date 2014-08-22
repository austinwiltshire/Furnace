""" Tests strategies and tests known metrics.

    REGRESSION style tests simply test that known outputs from the models
    Other tests have been hand checked generally using yahoo data. Yahoo data drifts, so usually download at one time
    and reuse that data over and over again.

    All written in py.test style.
    to run,

    pip install pytest

    in Furnace directory,
    >py.test
    """

from datetime import datetime
from furnace.data import asset, yahoo, fcalendar
from furnace import performance, strategy, portfolio
import numpy

def is_close(val, other_val):
    """ Checks two floating points are 'close enough'.

        A relative difference of 3 usually is 'close enough' given that we check against yahoo data a lot """
    return numpy.isclose(val, other_val, rtol=1e-03)

def make_default_asset_factory(symbols):
    """ Helper method returns an asset factory for a list of symbols with a calendar starting at 2000-1-1 """

    calendar = fcalendar.make_fcalendar(datetime(2000, 1, 1))
    data_cache = yahoo.load_pandas()
    return asset.AssetUniverse(symbols, data_cache, calendar)

def yahoo_adjusted_close_return(asset_, begin, end):
    """ Helper to calculate dividend and split adjusted total return using yahoo stats """
    adj_close = asset_.table()[asset_.table().index >= datetime(2003, 1, 2)]['Adj Close']
    first = adj_close[begin]
    last = adj_close[end]
    return (last - first) / first

def test_buy_and_hold_spy_cagr():
    """ Tests a buy and hold CAGR of the SPY from 1-2-3003 to 12-31-2012
    as of aug 18, validated with adj close from yahoo
    """
    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    asset_factory = make_default_asset_factory(["SPY"])

    test_strategy = strategy.buy_and_hold_stocks(asset_factory, begin, end)
    performance_ = performance.fire_furnace(test_strategy, begin, end)

    assert is_close(performance_.cagr(), 1.067)

def test_all_spy_index_total_return():
    """ Tests the total return of an all SPY index between 2003-1-2 and 2012-12-31 is same as yahoo adj return
        for same period """

    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    asset_factory = make_default_asset_factory(["SPY"])
    spy = asset_factory.make_asset("SPY")

    index = portfolio.make_index([portfolio.Weighting(spy, 1.0)], begin)
    adj_return = yahoo_adjusted_close_return(spy, begin, end)

    assert is_close(index.total_return_by(datetime(2012, 12, 31)), adj_return)

def test_all_lqd_index_total_return():
    """ Test that all lqd index has total return equal to yahoo adj close from 2003-1-2 to 2012-12-31 """

    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    asset_factory = make_default_asset_factory(["LQD"])
    lqd = asset_factory.make_asset("LQD")

    index = portfolio.make_index([portfolio.Weighting(lqd, 1.0)], begin)
    adj_return = yahoo_adjusted_close_return(lqd, begin, end)

    assert is_close(index.total_return_by(datetime(2012, 12, 31)), adj_return)

def test_buy_and_hold_spy_growth_by():
    """ Tests buy and hold single asset spy growth_by at multiple points between 2003-1-2 and 2012-12-31
    hand confirmed as of aug 18 using yahoo adj close """

    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    asset_factory = make_default_asset_factory(["SPY"])
    test_strategy = strategy.buy_and_hold_stocks(asset_factory, begin, end)

    performance_ = performance.fire_furnace(test_strategy, begin, end)

    assert is_close(performance_.growth_by(datetime(2003, 1, 2)), 1.00)
    assert is_close(performance_.growth_by(datetime(2004, 2, 2)), 1.272)
    assert is_close(performance_.growth_by(datetime(2005, 1, 3)), 1.368)
    assert is_close(performance_.growth_by(datetime(2012, 12, 31)), 1.906)

def test_bh_stocks_and_bonds_cagr():
    """ Tests buy and hold of two assets, spy and lqd, cagr metric from 2003-1-2 to 2012-12-31

        stocks and bonds strategy assumes static holding of 80% stocks and 20% bonds
        hand checked on august 20th """

    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    asset_factory = make_default_asset_factory(["SPY", "LQD"])
    test_strategy = strategy.buy_and_hold_stocks_and_bonds(asset_factory, begin, end)

    performance_ = performance.fire_furnace(test_strategy, begin, end)

    assert is_close(performance_.cagr(), 1.066)

def test_bh_stcks_n_bnds_growth_by():
    """ Tests buy and hold stocks and bonds strategy with two assets, spy and lqd, looking at growth by at multiple
        points between 2003-1-2 and 2012-12-31.

        hand checked august 20 against yahoo adj close """

    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    asset_factory = make_default_asset_factory(["SPY", "LQD"])
    test_strategy = strategy.buy_and_hold_stocks_and_bonds(asset_factory, begin, end)

    performance_ = performance.fire_furnace(test_strategy, begin, end)

    assert is_close(performance_.growth_by(datetime(2003, 1, 2)), 1.0)
    assert is_close(performance_.growth_by(datetime(2003, 2, 3)), 0.960)
    assert is_close(performance_.growth_by(datetime(2004, 1, 2)), 1.214)
    assert is_close(performance_.growth_by(datetime(2012, 12, 31)), 1.903)

def test_spy_lqd_mix_index_ttl_rtn():
    """ Test an index of 50% spy and 50% lqd, total_return_by, between 2003-1-2 and 2012-12-31
     hand calculated on aug 20th with yahoo adj close """

    #NOTE: Adjusted close floats with time, meaning with different data adjusted close changes even on the same
    #dates. This does not always seem geometrically stable as long term returns can shift even though they've
    #'already' happened. This is one benefit of using one stable understood system than relying on yahoo's black
    #magic adjusted close.

    asset_factory = make_default_asset_factory(["SPY", "LQD"])

    index = portfolio.make_index([portfolio.Weighting(asset_factory.make_asset("LQD"), 0.5),
                                  portfolio.Weighting(asset_factory.make_asset("SPY"), 0.5)],
                                 datetime(2003, 1, 2))

    assert is_close(index.total_return_by(datetime(2012, 12, 31)), .900)

def test_volatility():
    """ Tests volatility of a mixed stocks and bonds portfolio between 2003-1-2 adn 2012-12-31 """

    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    asset_factory = make_default_asset_factory(["SPY", "LQD"])
    test_strategy = strategy.buy_and_hold_stocks_and_bonds(asset_factory, begin, end)

    performance_ = performance.fire_furnace(test_strategy, begin, end)

    assert is_close(performance_.volatility(), 0.168)
