"""
Tests strategies
"""

from datetime import datetime
from furnace.data import fcalendar
from furnace import performance, strategy, portfolio, weathermen
from furnace.test.helpers import make_default_asset_factory, is_close, compound_growth, CALENDAR, DEFAULT_ASSET_FACTORY
import matplotlib

def compare(perf1, perf2):
    perf1.plot_index(100.0)
    perf2.plot_index(100.0)
    print perf1.cagr(), " ", perf1.simple_sharpe()
    print perf2.cagr(), " ", perf2.simple_sharpe()
    matplotlib.pyplot.show()

#TODO: look at making more specific names
def test_bh_stocks_and_bonds_cagr():
    """ Tests buy and hold of two assets, spy and lqd, cagr metric from 2003-1-2 to 2012-12-31

        stocks and bonds strategy assumes static holding of 80% stocks and 20% bonds
        hand checked on august 20th """

    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    test_strategy = strategy.buy_and_hold_stocks_and_bonds(DEFAULT_ASSET_FACTORY, begin, end, CALENDAR)

    performance_ = performance.fire_furnace(test_strategy, begin, end)

    assert is_close(performance_.cagr(), 0.0666)

def test_bh_stcks_n_bnds_growth_by():
    """ Tests buy and hold stocks and bonds strategy with two assets, spy and lqd, looking at growth by at multiple
        points between 2003-1-2 and 2012-12-31.

        hand checked august 20 against yahoo adj close """

    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    test_strategy = strategy.buy_and_hold_stocks_and_bonds(DEFAULT_ASSET_FACTORY, begin, end, CALENDAR)

    performance_ = performance.fire_furnace(test_strategy, begin, end)

    assert is_close(performance_.growth_by(begin), 0.0)
    assert is_close(performance_.growth_by(datetime(2003, 2, 3)), -0.0396)
    assert is_close(performance_.growth_by(datetime(2004, 1, 2)), 0.2144)
    assert is_close(performance_.growth_by(end), 0.903)

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

def test_daily_yearly_eq():
    """ Tests that a 365 day rebalancing rule is equivalent to a yearly rebalancing rule """
    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)

    daily = strategy.ndays_rebalance_multi_asset(DEFAULT_ASSET_FACTORY, CALENDAR, ["SPY", "LQD"], [.8, .2], 252)
    yearly = strategy.yearly_rebalance_multi_asset(DEFAULT_ASSET_FACTORY, CALENDAR, ["SPY", "LQD"], [.8, .2])

    daily_performance = performance.fire_furnace(daily, begin, end)
    yearly_performance = performance.fire_furnace(yearly, begin, end)

    assert is_close(daily_performance.cagr(), yearly_performance.cagr())

def test_single_yearly_daily():
    """ TDD for n-days rebalance rule. 10 day rebalance rule should be the same as buy and hold single asset
    We chose 10 days because 1 day rebalancing takes about 10 seconds to run. """

    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    rebalanced = strategy.ndays_rebalance_single_asset(DEFAULT_ASSET_FACTORY, CALENDAR, "SPY", 10)
    buy_and_hold = strategy.buy_and_hold_stocks(DEFAULT_ASSET_FACTORY, begin, end, CALENDAR)

    rebalanced_perf = performance.fire_furnace(rebalanced, begin, end)
    buy_and_hold_perf = performance.fire_furnace(buy_and_hold, begin, end)
    test_date = datetime(2011, 12, 30)

    assert is_close(rebalanced_perf.growth_by(test_date), buy_and_hold_perf.growth_by(test_date))

def test_v1_baseline():
    """ Test the october 26 2014 strategy regression style """

    perf = strategy.v1_baseline()

    assert is_close(perf.cagr(), 0.0693)
    assert is_close(perf.simple_sharpe(), 0.809)

def test_real_estate():
    """ Regression test on the real estate index IYR """
    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)

    strat = strategy.buy_and_hold_single_asset(DEFAULT_ASSET_FACTORY, begin, end, "IYR", CALENDAR)
    perf = strat.performance_during(begin, end)

    assert is_close(perf.cagr(), 0.0954)
    assert is_close(perf.simple_sharpe(), 0.2748)

def test_money_market():
    """ Regression test on the money market index SHV """
    begin = datetime(2007, 1, 11)
    end = datetime(2012, 12, 31)

    strat = strategy.buy_and_hold_single_asset(DEFAULT_ASSET_FACTORY, begin, end, "SHV", CALENDAR)
    perf = strat.performance_during(begin, end)

    assert is_close(perf.cagr(), 0.0136)
    assert is_close(perf.simple_sharpe(), 2.7199)

#TODO: 1.1 pull out repeated 'perfomance_test' function that takes in dates, symbol cagr and sharpe and does the below
#functionality
#TODO: 1.1 refactor to just test the asset's own cagr and simple sharpe rather than the buy and hold portfolio logic
#TODO: 1.1 move this to test_asset
def test_bull_dollar():
    """ Regression test on the bullish dollar index UUP """
    begin = datetime(2007, 3, 1)
    end = datetime(2012, 12, 31)

    strat = strategy.buy_and_hold_single_asset(DEFAULT_ASSET_FACTORY, begin, end, "UUP", CALENDAR)
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

def test_proportional_portfolio():
    """ Regression test of the proportional portfolio strategy with full history forecasts

    This strategy nets cagr of 0.0699 and SS of 0.7606, .0006 better and .0484 worse than current baseline
    respectively. It has the benefit of being based on a heuristic rather than a grid search of history.
    It has the drawback of still having clairvoyant bias (uses future data to predict the past).
    """
    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)

    strat = strategy.Strategy(
        portfolio.ProportionalWeighting(["SPY", "LQD"]),
        DEFAULT_ASSET_FACTORY,
        strategy.NDayRebalance(CALENDAR, 25),
        weathermen.HistoricalAverage()
    )

    perf = strat.performance_during(begin, end)

    assert is_close(perf.cagr(), 0.0699)
    assert is_close(perf.simple_sharpe(), 0.7606)

def test_period_average_w_reit():
    """ This is a regression test of using the 1 month momentum based forecaster. It *underperforms* both in cagr and
    simple sharpe the full history. I have hacked in place an anti-momentum one month rebalancing rule, and that ends
    up outperforming a 3 asset historical rebalance. The 2 asset anti-momentum still underperforms, though. This
    approach has the benefit of no clairvoyance, but at significant cost to simple sharpe. Additionally, this approach
    shows that adding real estate to our portfolio does, in fact, make our returns and simple sharpes worse against what
    financial theory of diversification might say but in favor of intuition given the bumpy ride real estate had during
    this period """

    begin = datetime(2004, 1, 2)
    end = datetime(2012, 12, 31)

    strat = strategy.Strategy(
        portfolio.ProportionalWeighting(["SPY", "LQD", "IYR"]),
        DEFAULT_ASSET_FACTORY,
        strategy.NDayRebalance(CALENDAR, 25),
        weathermen.PeriodAverage(CALENDAR)
    )

    perf = strat.performance_during(begin, end)

    assert is_close(perf.cagr(), 0.0585)
    assert is_close(perf.simple_sharpe(), .33762)


def test_currency_momentum():
    """ UUP, a bullish dollar currency etf, does surprisingly well with momentum whereas stocks tend to have a negative
    monthly autocorrelation. This is purely a regression test """
    begin = datetime(2007, 5, 1)
    end = datetime(2012, 12, 31)

    strat = strategy.Strategy(
        portfolio.ProportionalWeighting(["SPY", "LQD", "UUP"]),
        DEFAULT_ASSET_FACTORY,
        strategy.NDayRebalance(CALENDAR, 25),
        weathermen.PeriodAverage(CALENDAR)
    )

    perf = strat.performance_during(begin, end)

    assert is_close(perf.cagr(), 0.0664)
    assert is_close(perf.simple_sharpe(), .608)

def test_v1_mom():

    begin = datetime(2009, 3, 2)
    end = datetime(2012, 12, 31)

    strat = strategy.Strategy(
        portfolio.ProportionalWeighting(["SPY", "LQD", "UUP"]),
        DEFAULT_ASSET_FACTORY,
        strategy.NDayRebalance(CALENDAR, 25),
        weathermen.PeriodAverage(CALENDAR)
    )

    perf = strat.performance_during(begin, end)

    assert is_close(perf.cagr(), 0.098)
    assert is_close(perf.simple_sharpe(), 0.925)

def test_simple_linear_specific():
    """ UUP, LQD and SPY all using a simple linear regression per asset.
    Regression test"""

    begin = datetime(2007, 6, 4)
    end = datetime(2012, 12, 31)

    spy = DEFAULT_ASSET_FACTORY.make_asset("SPY")
    lqd = DEFAULT_ASSET_FACTORY.make_asset("LQD")
    uup = DEFAULT_ASSET_FACTORY.make_asset("UUP")

    spy_weatherman = weathermen.SimpleLinear(CALENDAR, spy)

    #The simple linear forecaster is actually really bad for lqd, so we use historical
    lqd_weatherman = weathermen.HistoricalAverage()
    uup_weatherman = weathermen.SimpleLinear(CALENDAR, uup)

    forecasts_dictionary = {spy: spy_weatherman, lqd: lqd_weatherman, uup: uup_weatherman}
    test_weatherman = weathermen.AssetSpecific(forecasts_dictionary)

    strat = strategy.Strategy(
        portfolio.ProportionalWeighting(["SPY", "LQD", "UUP"]),
        DEFAULT_ASSET_FACTORY,
        strategy.NDayRebalance(CALENDAR, 25),
        test_weatherman
    )

    perf = strat.performance_during(begin, end)

    assert is_close(perf.cagr(), 0.0542)
    assert is_close(perf.simple_sharpe(), 0.486)

#TODO: wasn't able to get to this. ARMA models work best with daily prices, and don't really get anything useful at all
#out of monthly prices. thus, we really need to go for a daily price model before we can add this test.
def test_arma():
    """ An attempt to use an arma model """
    pass
