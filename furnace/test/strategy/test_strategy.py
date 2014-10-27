"""
Tests strategies
"""

from datetime import datetime
from furnace.data import fcalendar
from furnace import performance, strategy
from furnace.test.helpers import make_default_asset_factory, is_close, compound_growth

#TODO: look at making more specific names
def test_bh_stocks_and_bonds_cagr():
    """ Tests buy and hold of two assets, spy and lqd, cagr metric from 2003-1-2 to 2012-12-31

        stocks and bonds strategy assumes static holding of 80% stocks and 20% bonds
        hand checked on august 20th """

    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    asset_factory = make_default_asset_factory(["SPY", "LQD"])
    calendar = fcalendar.make_fcalendar(datetime(2000, 1, 1))
    test_strategy = strategy.buy_and_hold_stocks_and_bonds(asset_factory, begin, end, calendar)

    performance_ = performance.fire_furnace(test_strategy, begin, end)

    assert is_close(performance_.cagr(), 0.0666)

def test_bh_stcks_n_bnds_growth_by():
    """ Tests buy and hold stocks and bonds strategy with two assets, spy and lqd, looking at growth by at multiple
        points between 2003-1-2 and 2012-12-31.

        hand checked august 20 against yahoo adj close """

    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    asset_factory = make_default_asset_factory(["SPY", "LQD"])
    calendar = fcalendar.make_fcalendar(datetime(2000, 1, 1))
    test_strategy = strategy.buy_and_hold_stocks_and_bonds(asset_factory, begin, end, calendar)

    performance_ = performance.fire_furnace(test_strategy, begin, end)

    assert is_close(performance_.growth_by(begin), 0.0)
    assert is_close(performance_.growth_by(datetime(2003, 2, 3)), -0.0396)
    assert is_close(performance_.growth_by(datetime(2004, 1, 2)), 0.2144)
    assert is_close(performance_.growth_by(end), 0.903)

def test_multi_asset_yearly_hand():
    """ Test that 4 year holding of multi asset rebalanced strategy is near what is hand calculated """

    calendar = fcalendar.make_fcalendar(datetime(2000, 1, 1))
    asset_factory = make_default_asset_factory(["SPY", "LQD"])
    begin = datetime(2003, 1, 2)
    end = datetime(2007, 1, 3)

    test_strategy = strategy.yearly_rebalance_multi_asset(asset_factory, calendar, ["SPY", "LQD"], [.8, .2])

    performance_ = performance.fire_furnace(test_strategy, begin, end)

    assert is_close(performance_.growth_by(end), 0.574)

def test_single_asset_yearly():
    """ TDD for single asset strategy but rebalanced yearly. Should be equivalent to buy and hold """

    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    calendar = fcalendar.make_fcalendar(datetime(2000, 1, 1))
    asset_factory = make_default_asset_factory(["SPY"])
    rebalanced = strategy.yearly_rebalance_single_asset(asset_factory, calendar, "SPY")
    buy_and_hold = strategy.buy_and_hold_stocks(asset_factory, begin, end, calendar)

    rebalanced_perf = performance.fire_furnace(rebalanced, begin, end)
    buy_and_hold_perf = performance.fire_furnace(buy_and_hold, begin, end)
    test_date = datetime(2011, 12, 30)

    assert is_close(rebalanced_perf.growth_by(test_date), buy_and_hold_perf.growth_by(test_date))

def test_multi_asset_yearly():
    """ TDD for multi asset - 80% spy, 20% lqd, rebalanced yearly. Should be equivalent to two years of
    buy and hold """

    calendar = fcalendar.make_fcalendar(datetime(2000, 1, 1))
    asset_factory = make_default_asset_factory(["SPY", "LQD"])

    year_2003 = datetime(2003, 1, 2)
    year_2004 = datetime(2004, 1, 2)
    year_2005 = datetime(2005, 1, 3)
    year_2006 = datetime(2006, 1, 3)

    test_strategy = strategy.yearly_rebalance_multi_asset(asset_factory, calendar, ["SPY", "LQD"], [.8, .2])
    performance_ = performance.fire_furnace(test_strategy, year_2003, year_2006)

    def get_buy_and_hold_perf(begin, end):
        """ Helper to get buy and hold strategy performance over a period """
        strat = strategy.buy_and_hold_stocks_and_bonds(asset_factory, begin, end, calendar)
        return performance.fire_furnace(strat, begin, end).growth_by(end)

    year_1_perf = get_buy_and_hold_perf(year_2003, year_2004)
    year_2_perf = get_buy_and_hold_perf(year_2004, year_2005)
    year_3_perf = get_buy_and_hold_perf(year_2005, year_2006)

    assert is_close(performance_.growth_by(year_2004), year_1_perf)
    assert is_close(performance_.growth_by(year_2005), compound_growth(year_1_perf, year_2_perf))
    assert is_close(performance_.growth_by(year_2006), compound_growth(year_1_perf, year_2_perf, year_3_perf))

def test_multi_asset_yearly_uneq():
    """ Test that holding a multi asset index with a yearly rebalance is *not* equal to the returns of a straight
    buy and hold """

    calendar = fcalendar.make_fcalendar(datetime(2000, 1, 1))
    asset_factory = make_default_asset_factory(["SPY", "LQD"])
    begin = datetime(2003, 1, 2)
    end = datetime(2006, 1, 3)

    rebalance = strategy.yearly_rebalance_multi_asset(asset_factory, calendar, ["SPY", "LQD"], [.8, .2])
    buy_and_hold = strategy.buy_and_hold_stocks_and_bonds(asset_factory, begin, end, calendar)

    rebalance_perf = performance.fire_furnace(rebalance, begin, end)
    buy_and_hold_perf = performance.fire_furnace(buy_and_hold, begin, end)

    assert not is_close(rebalance_perf.growth_by(end), buy_and_hold_perf.growth_by(end))

def test_daily_yearly_eq():
    """ Tests that a 365 day rebalancing rule is equivalent to a yearly rebalancing rule """
    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    calendar = fcalendar.make_fcalendar(datetime(2000, 1, 1))
    asset_factory = make_default_asset_factory(["SPY", "LQD"])

    daily = strategy.ndays_rebalance_multi_asset(asset_factory, calendar, ["SPY", "LQD"], [.8, .2], 252)
    yearly = strategy.yearly_rebalance_multi_asset(asset_factory, calendar, ["SPY", "LQD"], [.8, .2])

    daily_performance = performance.fire_furnace(daily, begin, end)
    yearly_performance = performance.fire_furnace(yearly, begin, end)

    assert is_close(daily_performance.cagr(), yearly_performance.cagr())

def test_single_yearly_daily():
    """ TDD for n-days rebalance rule. 10 day rebalance rule should be the same as buy and hold single asset
    We chose 10 days because 1 day rebalancing takes about 10 seconds to run. """

    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    calendar = fcalendar.make_fcalendar(datetime(2000, 1, 1))
    asset_factory = make_default_asset_factory(["SPY"])
    rebalanced = strategy.ndays_rebalance_single_asset(asset_factory, calendar, "SPY", 10)
    buy_and_hold = strategy.buy_and_hold_stocks(asset_factory, begin, end, calendar)

    rebalanced_perf = performance.fire_furnace(rebalanced, begin, end)
    buy_and_hold_perf = performance.fire_furnace(buy_and_hold, begin, end)
    test_date = datetime(2011, 12, 30)

    assert is_close(rebalanced_perf.growth_by(test_date), buy_and_hold_perf.growth_by(test_date))

def test_v1_baseline():
    """ Test the october 26 2014 strategy regression style """

    perf = strategy.v1_baseline()

    assert is_close(perf.cagr(), 0.0693)
    assert is_close(perf.simple_sharpe(), 0.809)
