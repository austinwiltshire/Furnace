"""
Tests strategies and tests known metrics.

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

#helpers
def is_close(val, other_val):
    """ Checks two floating points are 'close enough'.

        A relative difference of 3 usually is 'close enough' given that we check against yahoo data a lot """
    return numpy.isclose(val, other_val, rtol=1e-03)

def make_default_asset_factory(symbols):
    """ Helper method returns an asset factory for a list of symbols with a calendar starting at 2000-1-1 """

    calendar = fcalendar.make_fcalendar(datetime(2000, 1, 1))
    data_cache = yahoo.load_pandas()
    return asset.AssetUniverse(symbols, data_cache, calendar)

#tests
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

    index = portfolio.Weightings([portfolio.Weighting(spy, 1.0)]).make_index_on(begin)
    adj_return = spy.yahoo_adjusted_return(begin, end)

    assert is_close(index.total_return_by(end), adj_return)

def test_all_lqd_index_total_return():
    """ Test that all lqd index has total return equal to yahoo adj close from 2003-1-2 to 2012-12-31 """

    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    asset_factory = make_default_asset_factory(["LQD"])
    lqd = asset_factory.make_asset("LQD")

    index = portfolio.Weightings([portfolio.Weighting(lqd, 1.0)]).make_index_on(begin)
    adj_return = lqd.yahoo_adjusted_return(begin, end)

    assert is_close(index.total_return_by(end), adj_return)

def test_empty_mixed_index():
    """ Tests that an index of multiple assets but logically single is the same as a single asset index """

    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    asset_factory = make_default_asset_factory(["SPY", "LQD"])
    lqd = asset_factory.make_asset("LQD")
    spy = asset_factory.make_asset("SPY")

    index = portfolio.Weightings([portfolio.Weighting(spy, 0.0), portfolio.Weighting(lqd, 1.0)]).make_index_on(begin)
    index2 = portfolio.Weightings([portfolio.Weighting(lqd, 1.0)]).make_index_on(begin)

    assert is_close(index.total_return_by(end), index2.total_return_by(end))

def test_buy_and_hold_spy_growth_by():
    """ Tests buy and hold single asset spy growth_by at multiple points between 2003-1-2 and 2012-12-31
    hand confirmed as of aug 18 using yahoo adj close """

    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    asset_factory = make_default_asset_factory(["SPY"])
    test_strategy = strategy.buy_and_hold_stocks(asset_factory, begin, end)

    performance_ = performance.fire_furnace(test_strategy, begin, end)

    assert is_close(performance_.growth_by(begin), 1.00)
    assert is_close(performance_.growth_by(datetime(2004, 2, 2)), 1.272)
    assert is_close(performance_.growth_by(datetime(2005, 1, 3)), 1.368)
    assert is_close(performance_.growth_by(end), 1.906)

def test_period_ends():
    """ Test that returns line up across period ends and beginnings with expectations """
    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    asset_factory = make_default_asset_factory(["SPY"])
    calendar = fcalendar.make_fcalendar(datetime(2000, 1, 1))

    reference = strategy.buy_and_hold_stocks(asset_factory, begin, end)
    rebalanced = strategy.yearly_rebalance_single_asset(asset_factory, calendar, "SPY")

    periods = list(rebalanced.periods_during(begin, end))
    first_start = periods[0].begin()
    first_end = periods[0].end()
    second_start = periods[1].begin()
    second_end = periods[1].end()
    last_start = periods[-1].begin()
    last_end = periods[-1].end()

    reference_performance = performance.fire_furnace(reference, begin, end)
    rebalanced_performance = performance.fire_furnace(rebalanced, begin, end)

    def equivalent_performance(date):
        """ Checks that reference and rebalanced portfolio growth is the same """
        return is_close(reference_performance.growth_by(date), rebalanced_performance.growth_by(date))

    assert first_end == second_start

    assert equivalent_performance(first_start)
    assert equivalent_performance(first_end)
    assert equivalent_performance(second_start)
    assert equivalent_performance(second_end)
    assert equivalent_performance(last_start)
    assert equivalent_performance(last_end)

def test_first_day():
    """ Test that an annually rebalanced portfolio has as it's first day the first trading day """
    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    asset_factory = make_default_asset_factory(["SPY"])
    calendar = fcalendar.make_fcalendar(datetime(2000, 1, 1))

    rebalanced = strategy.yearly_rebalance_single_asset(asset_factory, calendar, "SPY")

    periods = list(rebalanced.periods_during(begin, end))
    first_start = periods[0].begin()

    assert first_start == begin

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

    assert is_close(performance_.growth_by(begin), 1.0)
    assert is_close(performance_.growth_by(datetime(2003, 2, 3)), 0.960)
    assert is_close(performance_.growth_by(datetime(2004, 1, 2)), 1.214)
    assert is_close(performance_.growth_by(end), 1.903)

def test_spy_lqd_mix_index_ttl_rtn():
    """ Test an index of 50% spy and 50% lqd, total_return_by, between 2003-1-2 and 2012-12-31
     hand calculated on aug 20th with yahoo adj close """

    #NOTE: Adjusted close floats with time, meaning with different data adjusted close changes even on the same
    #dates. This does not always seem geometrically stable as long term returns can shift even though they've
    #'already' happened. This is one benefit of using one stable understood system than relying on yahoo's black
    #magic adjusted close.

    asset_factory = make_default_asset_factory(["SPY", "LQD"])

    index = portfolio.Weightings([portfolio.Weighting(asset_factory.make_asset("LQD"), 0.5),
                                  portfolio.Weighting(asset_factory.make_asset("SPY"), 0.5)]).make_index_on(
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

def test_single_asset_yearly():
    """ TDD for single asset strategy but rebalanced yearly. Should be equivalent to buy and hold """

    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    calendar = fcalendar.make_fcalendar(datetime(2000, 1, 1))
    asset_factory = make_default_asset_factory(["SPY"])
    rebalanced = strategy.yearly_rebalance_single_asset(asset_factory, calendar, "SPY")
    buy_and_hold = strategy.buy_and_hold_stocks(asset_factory, begin, end)

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
        strat = strategy.buy_and_hold_stocks_and_bonds(asset_factory, begin, end)
        return performance.fire_furnace(strat, begin, end).growth_by(end)

    year_1_perf = get_buy_and_hold_perf(year_2003, year_2004)
    year_2_perf = get_buy_and_hold_perf(year_2004, year_2005)
    year_3_perf = get_buy_and_hold_perf(year_2005, year_2006)

    assert is_close(performance_.growth_by(year_2004), year_1_perf)
    assert is_close(performance_.growth_by(year_2005), year_1_perf * year_2_perf)
    assert is_close(performance_.growth_by(year_2006), year_1_perf * year_2_perf * year_3_perf)

def test_multi_asset_yearly_uneq():
    """ Test that holding a multi asset index with a yearly rebalance is *not* equal to the returns of a straight
    buy and hold """

    calendar = fcalendar.make_fcalendar(datetime(2000, 1, 1))
    asset_factory = make_default_asset_factory(["SPY", "LQD"])
    begin = datetime(2003, 1, 2)
    end = datetime(2006, 1, 3)

    rebalance = strategy.yearly_rebalance_multi_asset(asset_factory, calendar, ["SPY", "LQD"], [.8, .2])
    buy_and_hold = strategy.buy_and_hold_stocks_and_bonds(asset_factory, begin, end)

    rebalance_perf = performance.fire_furnace(rebalance, begin, end)
    buy_and_hold_perf = performance.fire_furnace(buy_and_hold, begin, end)

    assert not is_close(rebalance_perf.growth_by(end), buy_and_hold_perf.growth_by(end))

def test_multi_asset_yearly_hand():
    """ Test that 4 year holding of multi asset rebalanced strategy is near what is hand calculated """

    calendar = fcalendar.make_fcalendar(datetime(2000, 1, 1))
    asset_factory = make_default_asset_factory(["SPY", "LQD"])
    begin = datetime(2003, 1, 2)
    end = datetime(2007, 1, 3)

    test_strategy = strategy.yearly_rebalance_multi_asset(asset_factory, calendar, ["SPY", "LQD"], [.8, .2])

    performance_ = performance.fire_furnace(test_strategy, begin, end)

    assert is_close(performance_.growth_by(end), 1.573)

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
    buy_and_hold = strategy.buy_and_hold_stocks(asset_factory, begin, end)

    rebalanced_perf = performance.fire_furnace(rebalanced, begin, end)
    buy_and_hold_perf = performance.fire_furnace(buy_and_hold, begin, end)
    test_date = datetime(2011, 12, 30)

    assert is_close(rebalanced_perf.growth_by(test_date), buy_and_hold_perf.growth_by(test_date))

def test_nday_supports_end_period():
    """ Test that the last day of an nday trading period falls n absolute days after beginning if there is
    nothing but valid trading days in between """
    begin = datetime(2012, 1, 3)
    end = datetime(2012, 1, 31)
    calendar = fcalendar.make_fcalendar(datetime(2000, 1, 1))
    asset_factory = make_default_asset_factory(["SPY"])

    rebalanced = strategy.ndays_rebalance_single_asset(asset_factory, calendar, "SPY", 2)

    periods = list(rebalanced.periods_during(begin, end))

    #the end of the first period should be 2 trading days in, starting on the 3rd, so 2012, 1, 5
    assert periods[0].begin() == datetime(2012, 1, 3)
    assert periods[0].end() == datetime(2012, 1, 5)

def test_nday_correct_num_days():
    """ Tests that the correct number of days occur in a nday rebalance rule """
    begin = datetime(2012, 1, 3)
    end = datetime(2012, 1, 31)
    calendar = fcalendar.make_fcalendar(datetime(2000, 1, 1))
    ndays = 5

    rule = strategy.NDayRebalance(calendar, ndays)
    periods = list(rule.periods_during(begin, end))
    assert all(calendar.trading_days_between(period.begin(), period.end()) == ndays for period in periods)

def test_nday_weekends():
    """ Tests that the nday rule falls across weekends appropritately by not counting them in the nday rule """
    begin = datetime(2012, 1, 6)
    end = datetime(2012, 1, 31)
    calendar = fcalendar.make_fcalendar(datetime(2000, 1, 1))
    ndays = 5

    rule = strategy.NDayRebalance(calendar, ndays)
    first_period = list(rule.periods_during(begin, end))[0]
    assert first_period.begin() == datetime(2012, 1, 6)
    assert first_period.end() == datetime(2012, 1, 13)

def test_nday_holidays():
    """ Tests that the nday rule falls across holidays appropriately by not countint them in the nday rule """
    begin = datetime(2011, 12, 30)
    end = datetime(2012, 1, 31)
    calendar = fcalendar.make_fcalendar(datetime(2000, 1, 1))
    ndays = 5

    rule = strategy.NDayRebalance(calendar, ndays)
    first_period = list(rule.periods_during(begin, end))[0]
    assert first_period.begin() == datetime(2011, 12, 30)
    assert first_period.end() == datetime(2012, 1, 9)

def test_nday_begin_end():
    """ Tests that the nday rule includes begin date as it's own first date, and end date as an end date when valid """
    begin = datetime(2012, 1, 3)
    end = datetime(2012, 2, 1)
    calendar = fcalendar.make_fcalendar(datetime(2000, 1, 1))
    ndays = 5

    rule = strategy.NDayRebalance(calendar, ndays)
    first_period = list(rule.periods_during(begin, end))[0]
    last_period = list(rule.periods_during(begin, end))[-1]
    assert first_period.begin() == begin
    assert last_period.end() == end

def test_annual_begin_end():
    """ Tests that the annual rule includes begin and end dates when they're valid """
    begin = datetime(2001, 1, 3)
    end = datetime(2013, 1, 3)
    calendar = fcalendar.make_fcalendar(datetime(2000, 1, 1))

    rule = strategy.AnnualRebalance(calendar)
    first_period = list(rule.periods_during(begin, end))[0]
    last_period = list(rule.periods_during(begin, end))[-1]
    assert first_period.begin() == begin
    assert last_period.end() == end

def test_annual_no_dates():
    """ Tests that the annual rule is empty when it includes not a full period """
    begin = datetime(2001, 1, 3)
    end = datetime(2001, 1, 4)
    calendar = fcalendar.make_fcalendar(datetime(2000, 1, 1))

    rule = strategy.AnnualRebalance(calendar)
    periods = list(rule.periods_during(begin, end))
    assert len(periods) == 0

def test_annual_no_dates_same_day():
    """ Tests that the annual rule is empty when it has the same begin and end """
    begin = datetime(2001, 1, 3)
    end = datetime(2001, 1, 3)
    calendar = fcalendar.make_fcalendar(datetime(2000, 1, 1))

    rule = strategy.AnnualRebalance(calendar)
    periods = list(rule.periods_during(begin, end))
    assert len(periods) == 0

def test_ndays_no_dates():
    """ Tests that the annual rule is empty when it includes not a full period """
    begin = datetime(2001, 1, 3)
    end = datetime(2001, 1, 4)
    calendar = fcalendar.make_fcalendar(datetime(2000, 1, 1))

    rule = strategy.NDayRebalance(calendar, 5)
    periods = list(rule.periods_during(begin, end))
    assert len(periods) == 0

def test_ndays_no_dates_same_day():
    """ Tests that the annual rule is empty when it has the same begin and end """
    begin = datetime(2001, 1, 3)
    end = datetime(2001, 1, 3)
    calendar = fcalendar.make_fcalendar(datetime(2000, 1, 1))

    rule = strategy.NDayRebalance(calendar, 5)
    periods = list(rule.periods_during(begin, end))
    assert len(periods) == 0

def test_yearly_correct_num_days():
    """ Tests that the correct number of days occur in a nday rebalance rule """
    begin = datetime(2003, 1, 3)
    end = datetime(2012, 12, 31)
    calendar = fcalendar.make_fcalendar(datetime(2000, 1, 1))
    ndays = 252

    rule = strategy.AnnualRebalance(calendar)
    periods = list(rule.periods_during(begin, end))
    assert all(abs(calendar.trading_days_between(period.begin(), period.end()) - ndays) < 3 for period in periods)

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
    asset_factory = make_default_asset_factory(["SPY"])
    buy_and_hold = strategy.buy_and_hold_single_asset(asset_factory, begin, end, "SPY")

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
