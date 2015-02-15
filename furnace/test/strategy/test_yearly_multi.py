" Tests strategies with a rebalancing rate of a year holding multiple assets "

from datetime import datetime
from furnace import strategy
from furnace.test.helpers import is_close, compound_growth, CALENDAR, DEFAULT_ASSET_FACTORY

def test_multi_asset_yearly_hand():
    """ Test that 4 year holding of multi asset rebalanced strategy is near what is hand calculated """

    begin = datetime(2003, 1, 2)
    end = datetime(2007, 1, 3)

    universe = DEFAULT_ASSET_FACTORY.make_universe(["SPY", "LQD"])

    test_strategy = strategy.yearly_rebalance_multi_asset(universe, CALENDAR, {"SPY": .8, "LQD": .2})

    performance_ = test_strategy.performance_during(begin, end)

    assert is_close(performance_.growth_by(end), 0.574)

def test_single_asset_yearly():
    """ TDD for single asset strategy but rebalanced yearly. Should be equivalent to buy and hold """

    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    universe = DEFAULT_ASSET_FACTORY.make_universe(["SPY"])
    rebalanced = strategy.yearly_rebalance_single_asset(universe, CALENDAR, "SPY")
    buy_and_hold = strategy.buy_and_hold_stocks(universe, begin, end, CALENDAR)

    rebalanced_perf = rebalanced.performance_during(begin, end)
    buy_and_hold_perf = buy_and_hold.performance_during(begin, end)
    test_date = datetime(2011, 12, 30)

    assert is_close(rebalanced_perf.growth_by(test_date), buy_and_hold_perf.growth_by(test_date))

def test_multi_asset_yearly():
    """ TDD for multi asset - 80% spy, 20% lqd, rebalanced yearly. Should be equivalent to two years of
    buy and hold """


    year_2003 = datetime(2003, 1, 2)
    year_2004 = datetime(2004, 1, 2)
    year_2005 = datetime(2005, 1, 3)
    year_2006 = datetime(2006, 1, 3)

    universe = DEFAULT_ASSET_FACTORY.make_universe(["SPY", "LQD"])
    test_strategy = strategy.yearly_rebalance_multi_asset(universe, CALENDAR, {"SPY": .8, "LQD": .2})
    performance_ = test_strategy.performance_during(year_2003, year_2006)

    def get_buy_and_hold_perf(begin, end):
        """ Helper to get buy and hold strategy performance over a period """
        strat = strategy.buy_and_hold_stocks_and_bonds(universe, begin, end, CALENDAR)
        return strat.performance_during(begin, end).growth_by(end)

    year_1_perf = get_buy_and_hold_perf(year_2003, year_2004)
    year_2_perf = get_buy_and_hold_perf(year_2004, year_2005)
    year_3_perf = get_buy_and_hold_perf(year_2005, year_2006)

    assert is_close(performance_.growth_by(year_2004), year_1_perf)
    assert is_close(performance_.growth_by(year_2005), compound_growth(year_1_perf, year_2_perf))
    assert is_close(performance_.growth_by(year_2006), compound_growth(year_1_perf, year_2_perf, year_3_perf))

def test_multi_asset_yearly_uneq():
    """ Test that holding a multi asset index with a yearly rebalance is *not* equal to the returns of a straight
    buy and hold """

    begin = datetime(2003, 1, 2)
    end = datetime(2006, 1, 3)

    universe = DEFAULT_ASSET_FACTORY.make_universe(["SPY", "LQD"])
    rebalance = strategy.yearly_rebalance_multi_asset(universe, CALENDAR, {"SPY": .8, "LQD": .2})
    buy_and_hold = strategy.buy_and_hold_stocks_and_bonds(universe, begin, end, CALENDAR)

    rebalance_perf = rebalance.performance_during(begin, end)
    buy_and_hold_perf = buy_and_hold.performance_during(begin, end)

    assert not is_close(rebalance_perf.growth_by(end), buy_and_hold_perf.growth_by(end))

