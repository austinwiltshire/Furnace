""" Tests performance metrics """

from datetime import datetime
from furnace import strategy
from furnace.test.helpers import make_default_asset_factory, is_close, CALENDAR, DEFAULT_ASSET_FACTORY
from furnace import performance


#TODO: mentioned elsewhere, but i really just need a single set of canned fake performance data that have
#hand calculated metrics on. all of the rest of this can be put under either integration (for hand checked)
#or regression tests

def test_cagr():
    """ Tests a buy and hold CAGR of the SPY from 1-2-3003 to 12-31-2012
    as of aug 18, validated with adj close from yahoo
    """
    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)

    universe = DEFAULT_ASSET_FACTORY.make_universe(["SPY"])

    test_strategy = strategy.buy_and_hold_stocks(universe, begin, end, CALENDAR)
    performance_ = test_strategy.performance_during(begin, end)

    assert is_close(performance_.cagr(), 0.0667)

    #Buy and hold only pays 2 comissions which are trivial at 100
    assert is_close(performance.commission_adj_cagr(CALENDAR, performance_, 100000.00, 7.00), 0.0667)

    #But they add up at 100 dollars.
    #NOTE: REGRESSION TEST
    assert is_close(performance.commission_adj_cagr(CALENDAR, performance_, 100.00, 7.00), 0.0548)

def test_growth_by():
    """ Tests buy and hold single asset spy growth_by at multiple points between 2003-1-2 and 2012-12-31
    hand confirmed as of aug 18 using yahoo adj close """

    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    universe = DEFAULT_ASSET_FACTORY.make_universe(["SPY"])
    test_strategy = strategy.buy_and_hold_stocks(universe, begin, end, CALENDAR)

    performance_ = test_strategy.performance_during(begin, end)

    assert is_close(performance_.growth_by(begin), 0.00)
    assert is_close(performance_.growth_by(datetime(2004, 2, 2)), 0.272)
    assert is_close(performance_.growth_by(datetime(2005, 1, 3)), 0.368)
    assert is_close(performance_.growth_by(end), 0.906)

def test_volatility():
    """ Tests volatility of a mixed stocks and bonds portfolio between 2003-1-2 adn 2012-12-31 """

    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    universe = DEFAULT_ASSET_FACTORY.make_universe(["SPY", "LQD"])
    test_strategy = strategy.buy_and_hold_stocks_and_bonds(universe, begin, end, CALENDAR)

    performance_ = test_strategy.performance_during(begin, end)

    assert is_close(performance_.volatility(), 0.168)

    #Volatility is more shakey for portfolio's more sensitive to comissions
    #NOTE: regression test
    assert is_close(performance.commission_adj_volatility(performance_, 100.00, 7.00), 0.1696)

def test_simple_sharpe():
    """ Regression test of simplified sharpe ratio """
    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    universe = DEFAULT_ASSET_FACTORY.make_universe(["SPY"])
    rebalanced = strategy.ndays_rebalance_single_asset(universe, CALENDAR, "SPY", 10)

    rebalanced_perf = rebalanced.performance_during(begin, end)

    assert is_close(rebalanced_perf.simple_sharpe(), .329)

    #Comission adjusted simple sharpe should be lower for comissions sensitive portfolios
    assert is_close(performance.commission_adj_simple_sharpe(CALENDAR, rebalanced_perf, 100.00, 7.00), .2710)

def test_number_of_trades_buyhold():
    """ Buy and hold of one single asset should have two trades, one entry and one exit """
    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)

    universe = DEFAULT_ASSET_FACTORY.make_universe(["SPY"])
    spy = universe["SPY"]
    buy_and_hold = strategy.buy_and_hold_single_asset(universe, begin, end, spy, CALENDAR)

    buy_and_hold_perf = buy_and_hold.performance_during(begin, end)

    assert buy_and_hold_perf.number_of_trades() == 2
    #TODO: grab the trade table here and assert that the first trade is on begin and the last trade is on
    #end

def test_number_of_trades_ndaily():
    """ Regression test of a more aggressive rebalancing rule regarding number of trades """
    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)

    universe = DEFAULT_ASSET_FACTORY.make_universe(["SPY", "LQD"])
    rebalanced = strategy.ndays_rebalance_multi_asset(universe, CALENDAR, {"SPY": .8, "LQD": .2}, 10)

    rebalanced_perf = rebalanced.performance_during(begin, end)

    assert rebalanced_perf.number_of_trades() == 504

def test_number_of_trades_yearly():
    """ Test that we have the correct number of trades over a 3 year period - 1 to buy in, 2 to trade, 1
    to sell out for 2 assets each for a total of (1 + 2 + 1) * 2 = 8"""

    begin = datetime(2003, 1, 2)
    end = datetime(2006, 1, 3)

    universe = DEFAULT_ASSET_FACTORY.make_universe(["SPY", "LQD"])
    rebalance = strategy.yearly_rebalance_multi_asset(universe, CALENDAR, {"SPY": .8, "LQD": .2})

    rebalance_perf = rebalance.performance_during(begin, end)

    assert rebalance_perf.number_of_trades() == 8

def test_actual_performance():
    """ Test that actual performance of 100,000 in  mixed stocks and bonds portfolio, 80% stocks 20%
    stocks, is X after comissions of 7 dollars a trade are taken into account """

    begin = datetime(2003, 1, 2)
    end = datetime(2004, 1, 5)

    universe = DEFAULT_ASSET_FACTORY.make_universe(["SPY", "LQD"])
    rebalance = strategy.yearly_rebalance_multi_asset(universe, CALENDAR, {"SPY": .8, "LQD": .2})

    rebalance_perf = rebalance.performance_during(begin, end)

    #assumptions
    total_return = .2143536 #regression
    number_of_trades = 4 #hand checked
    assert is_close(rebalance_perf.total_return(), total_return)
    assert rebalance_perf.number_of_trades() == number_of_trades

    principle = 100000.00
    actual_growth = principle * (1.0 + total_return)
    assert is_close(rebalance_perf.growth_curve(100000.00, 0.00).ix[-1], actual_growth)

    comissions = 10.00
    total_comissions = number_of_trades * comissions
    assert is_close(rebalance_perf.growth_curve(100000.00, 10.00).ix[-1], actual_growth - total_comissions)

def test_actual_performance_2years():
    """ Test that actual performance of 100,000 in  mixed stocks and bonds portfolio, 80% stocks 20%
    stocks, is X after comissions of 7 dollars a trade are taken into account """

    begin = datetime(2003, 1, 2)
    end = datetime(2005, 1, 5)

    universe = DEFAULT_ASSET_FACTORY.make_universe(["SPY", "LQD"])
    rebalance = strategy.yearly_rebalance_multi_asset(universe, CALENDAR, {"SPY": .8, "LQD": .2})

    rebalance_perf = rebalance.performance_during(begin, end)

    #assumptions
    total_return = .33114 #regression
    number_of_trades = 6 #hand checked
    assert is_close(rebalance_perf.total_return(), total_return)
    assert rebalance_perf.number_of_trades() == number_of_trades

    principle = 10000.00
    actual_growth = principle * (1.0 + total_return)
    assert is_close(rebalance_perf.growth_curve(principle, 0.00).ix[-1], actual_growth)

    comissions = 10.00

    growth_first_year = 0.2143536
    growth_second_year = 0.096177

    #hand calculate principle, take out comissions then do return per year
    principle = 10000.00
    calculated_principle = principle
    calculated_principle -= comissions * 2
    calculated_principle *= (1.0 + growth_first_year)
    calculated_principle -= comissions * 2
    calculated_principle *= (1.0 + growth_second_year)
    calculated_principle -= comissions * 2

    assert is_close(rebalance_perf.growth_curve(principle, comissions).ix[-1], calculated_principle)
