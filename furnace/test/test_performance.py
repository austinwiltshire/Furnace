""" Tests performance metrics """

from datetime import datetime
from furnace.data import fcalendar
from furnace import performance, strategy
from furnace.test.helpers import make_default_asset_factory, is_close, compound_growth

#TODO: look at making more specific names
def test_buy_and_hold_spy_cagr():
    """ Tests a buy and hold CAGR of the SPY from 1-2-3003 to 12-31-2012
    as of aug 18, validated with adj close from yahoo
    """
    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    calendar = fcalendar.make_fcalendar(datetime(2000, 1, 1))
    asset_factory = make_default_asset_factory(["SPY"])

    test_strategy = strategy.buy_and_hold_stocks(asset_factory, begin, end, calendar)
    performance_ = performance.fire_furnace(test_strategy, begin, end)

    assert is_close(performance_.cagr(), 0.0667)

def test_buy_and_hold_spy_growth_by():
    """ Tests buy and hold single asset spy growth_by at multiple points between 2003-1-2 and 2012-12-31
    hand confirmed as of aug 18 using yahoo adj close """

    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    calendar = fcalendar.make_fcalendar(datetime(2000, 1, 1))
    asset_factory = make_default_asset_factory(["SPY"])
    test_strategy = strategy.buy_and_hold_stocks(asset_factory, begin, end, calendar)

    performance_ = performance.fire_furnace(test_strategy, begin, end)

    assert is_close(performance_.growth_by(begin), 0.00)
    assert is_close(performance_.growth_by(datetime(2004, 2, 2)), 0.272)
    assert is_close(performance_.growth_by(datetime(2005, 1, 3)), 0.368)
    assert is_close(performance_.growth_by(end), 0.906)

def test_volatility():
    """ Tests volatility of a mixed stocks and bonds portfolio between 2003-1-2 adn 2012-12-31 """

    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    asset_factory = make_default_asset_factory(["SPY", "LQD"])
    calendar = fcalendar.make_fcalendar(datetime(2000, 1, 1))
    test_strategy = strategy.buy_and_hold_stocks_and_bonds(asset_factory, begin, end, calendar)

    performance_ = performance.fire_furnace(test_strategy, begin, end)

    assert is_close(performance_.volatility(), 0.168)

def test_simple_sharpe():
    """ Regression test of simplified sharpe ratio """
    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    calendar = fcalendar.make_fcalendar(datetime(2000, 1, 1))
    asset_factory = make_default_asset_factory(["SPY"])
    rebalanced = strategy.ndays_rebalance_single_asset(asset_factory, calendar, "SPY", 10)

    rebalanced_perf = performance.fire_furnace(rebalanced, begin, end)

    assert is_close(rebalanced_perf.simple_sharpe(), .329)

def test_number_of_trades_buyhold():
    """ Buy and hold of one single asset should have one single trade date """
    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    calendar = fcalendar.make_fcalendar(datetime(2000, 1, 1))
    asset_factory = make_default_asset_factory(["SPY"])
    buy_and_hold = strategy.buy_and_hold_single_asset(asset_factory, begin, end, "SPY", calendar)

    buy_and_hold_perf = performance.fire_furnace(buy_and_hold, begin, end)

    assert buy_and_hold_perf.number_of_trades() == 1

def test_number_of_trades_ndaily():
    """ Regression test of a more aggressive rebalancing rule regarding number of trades """
    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    calendar = fcalendar.make_fcalendar(datetime(2000, 1, 1))
    asset_factory = make_default_asset_factory(["SPY"])
    rebalanced = strategy.ndays_rebalance_single_asset(asset_factory, calendar, "SPY", 10)

    rebalanced_perf = performance.fire_furnace(rebalanced, begin, end)

    assert rebalanced_perf.number_of_trades() == 251
