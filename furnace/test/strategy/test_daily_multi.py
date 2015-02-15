" Tests strategies whos rebalancing rate is in number of days which hold multiple assets "

from datetime import datetime
from furnace import strategy
from furnace.test.helpers import is_close, CALENDAR, DEFAULT_ASSET_FACTORY

def test_daily_yearly_eq():
    """ Tests that a 365 day rebalancing rule is equivalent to a yearly rebalancing rule """
    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)

    universe = DEFAULT_ASSET_FACTORY.make_universe(["SPY", "LQD"])

    weightings = {"SPY": .8, "LQD": .2}
    daily = strategy.ndays_rebalance_multi_asset(universe, CALENDAR, weightings, 252)
    yearly = strategy.yearly_rebalance_multi_asset(universe, CALENDAR, weightings)

    daily_performance = daily.performance_during(begin, end)
    yearly_performance = yearly.performance_during(begin, end)

    assert is_close(daily_performance.cagr(), yearly_performance.cagr())

def test_single_yearly_daily():
    """ TDD for n-days rebalance rule. 10 day rebalance rule should be the same as buy and hold single asset
    We chose 10 days because 1 day rebalancing takes about 10 seconds to run. """

    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    universe = DEFAULT_ASSET_FACTORY.make_universe(["SPY"])
    rebalanced = strategy.ndays_rebalance_single_asset(universe, CALENDAR, "SPY", 10)
    buy_and_hold = strategy.buy_and_hold_stocks(universe, begin, end, CALENDAR)

    rebalanced_perf = rebalanced.performance_during(begin, end)
    buy_and_hold_perf = buy_and_hold.performance_during(begin, end)
    test_date = datetime(2011, 12, 30)

    assert is_close(rebalanced_perf.growth_by(test_date), buy_and_hold_perf.growth_by(test_date))

def test_v1_baseline():
    """ Test the october 26 2014 strategy regression style """

    perf = strategy.v1_baseline()

    assert is_close(perf.cagr(), 0.0693)
    assert is_close(perf.simple_sharpe(), 0.809)

