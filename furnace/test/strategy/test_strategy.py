"""
Tests strategies. This might include tests of the instruments of strategies, such as portfolio optimizers,
forecasts, etc., but ultimately is about the overall strategy and it's performance.
"""

#TODO: should this module be moved into something like labs instead of test? It's primarily exploratory 
#integration regression tests

from datetime import datetime
from furnace import strategy, portfolio, weathermen
from furnace.test.helpers import is_close, CALENDAR, DEFAULT_ASSET_FACTORY
import matplotlib

def compare(perf1, perf2):
    """ Helper function that compares two strategies performances """

    perf1.plot_index(100.0)
    perf2.plot_index(100.0)
    print perf1.cagr(), " ", perf1.simple_sharpe()
    print perf2.cagr(), " ", perf2.simple_sharpe()
    matplotlib.pyplot.show()

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

def test_period_average_reit():
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


def test_period_average_currency():
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

def test_currency_no_crash():
    " A regression test of the same strategy as above but taking the 2008 crash out "

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
