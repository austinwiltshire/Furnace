" Tests strategies with a rebalancing rate of a year holding multiple assets "

from datetime import datetime
from furnace.data import fcalendar
from furnace import performance, strategy, portfolio, weathermen
from furnace.test.helpers import make_default_asset_factory, is_close, compound_growth, CALENDAR, DEFAULT_ASSET_FACTORY
import matplotlib

def test_multi_asset_yearly_hand():
    """ Test that 4 year holding of multi asset rebalanced strategy is near what is hand calculated """

    begin = datetime(2003, 1, 2)
    end = datetime(2007, 1, 3)

    test_strategy = strategy.yearly_rebalance_multi_asset(DEFAULT_ASSET_FACTORY, CALENDAR, ["SPY", "LQD"], [.8, .2])

    performance_ = performance.fire_furnace(test_strategy, begin, end)

    assert is_close(performance_.growth_by(end), 0.574)

def test_single_asset_yearly():
    """ TDD for single asset strategy but rebalanced yearly. Should be equivalent to buy and hold """

    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    rebalanced = strategy.yearly_rebalance_single_asset(DEFAULT_ASSET_FACTORY, CALENDAR, "SPY")
    buy_and_hold = strategy.buy_and_hold_stocks(DEFAULT_ASSET_FACTORY, begin, end, CALENDAR)

    rebalanced_perf = performance.fire_furnace(rebalanced, begin, end)
    buy_and_hold_perf = performance.fire_furnace(buy_and_hold, begin, end)
    test_date = datetime(2011, 12, 30)

    assert is_close(rebalanced_perf.growth_by(test_date), buy_and_hold_perf.growth_by(test_date))

def test_multi_asset_yearly():
    """ TDD for multi asset - 80% spy, 20% lqd, rebalanced yearly. Should be equivalent to two years of
    buy and hold """


    year_2003 = datetime(2003, 1, 2)
    year_2004 = datetime(2004, 1, 2)
    year_2005 = datetime(2005, 1, 3)
    year_2006 = datetime(2006, 1, 3)

    test_strategy = strategy.yearly_rebalance_multi_asset(DEFAULT_ASSET_FACTORY, CALENDAR, ["SPY", "LQD"], [.8, .2])
    performance_ = performance.fire_furnace(test_strategy, year_2003, year_2006)

    def get_buy_and_hold_perf(begin, end):
        """ Helper to get buy and hold strategy performance over a period """
        strat = strategy.buy_and_hold_stocks_and_bonds(DEFAULT_ASSET_FACTORY, begin, end, CALENDAR)
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

    begin = datetime(2003, 1, 2)
    end = datetime(2006, 1, 3)

    rebalance = strategy.yearly_rebalance_multi_asset(DEFAULT_ASSET_FACTORY, CALENDAR, ["SPY", "LQD"], [.8, .2])
    buy_and_hold = strategy.buy_and_hold_stocks_and_bonds(DEFAULT_ASSET_FACTORY, begin, end, CALENDAR)

    rebalance_perf = performance.fire_furnace(rebalance, begin, end)
    buy_and_hold_perf = performance.fire_furnace(buy_and_hold, begin, end)

    assert not is_close(rebalance_perf.growth_by(end), buy_and_hold_perf.growth_by(end))

