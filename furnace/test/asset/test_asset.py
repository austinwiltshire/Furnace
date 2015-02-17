"""

Tests the asset helper class

"""

from furnace.test.helpers import is_close, DEFAULT_ASSET_FACTORY, CALENDAR
from datetime import datetime
from furnace.data.asset import adjust_period, annualized
from furnace import strategy

def test_splits():
    """ Tests that splits are handled correctly.

    There was a split issued on jun 9th 2005 on the stock IYR. Close on the 8th was 126.66, divided by 2
    yields 63.33. The stock closed at 63.34 on the 10th, for a .0158% return 8 to june 10th

    """

    iyr = DEFAULT_ASSET_FACTORY.make_asset("IYR")

    assert is_close(iyr.total_return(datetime(2005, 6, 8), datetime(2005, 6, 10)), .000158)

def test_adjust_period():
    """ Tests that period arithmatic is correct """

    assert is_close(adjust_period(0.055, 20, 252), annualized(.055, 20))
    assert is_close(adjust_period(0.6, 20, 1), 0.02378)

#TODO: change these to simply look at the total return of these assets between two dates. no reason
#to run a whole performance during
def test_real_estate():
    """ Regression test on the real estate index IYR """
    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)

    universe = DEFAULT_ASSET_FACTORY.make_universe(["IYR"])
    iyr = universe['IYR']
    strat = strategy.buy_and_hold_single_asset(universe, begin, end, iyr, CALENDAR)
    perf = strat.performance_during(begin, end)

    assert is_close(perf.cagr(), 0.0954)
    assert is_close(perf.simple_sharpe(), 0.2748)

def test_money_market():
    """ Regression test on the money market index SHV """
    begin = datetime(2007, 1, 11)
    end = datetime(2012, 12, 31)

    universe = DEFAULT_ASSET_FACTORY.make_universe(["SHV"])
    shv = universe['SHV']
    strat = strategy.buy_and_hold_single_asset(universe, begin, end, shv, CALENDAR)
    perf = strat.performance_during(begin, end)

    assert is_close(perf.cagr(), 0.0136)
    assert is_close(perf.simple_sharpe(), 2.7199)

#TODO: 1.1 pull out repeated 'perfomance_test' function that takes in dates, symbol cagr and sharpe and does the below
#functionality
#TODO: 1.1 refactor to just test the asset's own cagr and simple sharpe rather than the buy and hold portfolio logic
#TODO: 1.1 move this to test_asset
def test_bull_dollar_currency():
    """ Regression test on the bullish dollar index UUP """
    begin = datetime(2007, 3, 1)
    end = datetime(2012, 12, 31)

    universe = DEFAULT_ASSET_FACTORY.make_universe(["UUP"])
    uup = universe['UUP']
    strat = strategy.buy_and_hold_single_asset(universe, begin, end, uup, CALENDAR)
    perf = strat.performance_during(begin, end)

    assert is_close(perf.cagr(), -0.0204)
    assert is_close(perf.simple_sharpe(), -0.2034)

def test_commodities():
    """ Regression test on the commodities tracking index GSG """
    begin = datetime(2006, 7, 21)
    end = datetime(2012, 12, 31)
    gsg = DEFAULT_ASSET_FACTORY.make_asset("GSG")

    assert is_close(gsg.total_return(begin, end), -.3342)
    assert is_close(gsg.volatility(begin, end), .2755)
