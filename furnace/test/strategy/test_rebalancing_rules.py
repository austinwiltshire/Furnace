"""
Tests behavior of the various rebalancing rules
"""

from datetime import datetime
from furnace.data import fcalendar
from furnace import performance, strategy
from furnace.test.helpers import make_default_asset_factory, is_close, CALENDAR, DEFAULT_ASSET_FACTORY

#TODO: look at making more specific names
def test_period_ends():
    """ Test that returns line up across period ends and beginnings with expectations """
    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)

    reference = strategy.buy_and_hold_stocks(DEFAULT_ASSET_FACTORY, begin, end, CALENDAR)
    rebalanced = strategy.yearly_rebalance_single_asset(DEFAULT_ASSET_FACTORY, CALENDAR, "SPY")

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

    rebalanced = strategy.yearly_rebalance_single_asset(DEFAULT_ASSET_FACTORY, CALENDAR, "SPY")

    periods = list(rebalanced.periods_during(begin, end))
    first_start = periods[0].begin()

    assert first_start == begin


def test_nday_supports_end_period():
    """ Test that the last day of an nday trading period falls n absolute days after beginning if there is
    nothing but valid trading days in between """
    begin = datetime(2012, 1, 3)
    end = datetime(2012, 1, 31)

    rebalanced = strategy.ndays_rebalance_single_asset(DEFAULT_ASSET_FACTORY, CALENDAR, "SPY", 2)

    periods = list(rebalanced.periods_during(begin, end))

    #the end of the first period should be 2 trading days in, starting on the 3rd, so 2012, 1, 5
    assert periods[0].begin() == datetime(2012, 1, 3)
    assert periods[0].end() == datetime(2012, 1, 5)

def test_nday_correct_num_days():
    """ Tests that the correct number of days occur in a nday rebalance rule """
    begin = datetime(2012, 1, 3)
    end = datetime(2012, 1, 31)
    ndays = 5

    rule = strategy.NDayRebalance(CALENDAR, ndays)
    periods = list(rule.periods_during(begin, end))
    assert all(CALENDAR.trading_days_between(period.begin(), period.end()) == ndays for period in periods)

def test_nday_weekends():
    """ Tests that the nday rule falls across weekends appropritately by not counting them in the nday rule """
    begin = datetime(2012, 1, 6)
    end = datetime(2012, 1, 31)
    ndays = 5

    rule = strategy.NDayRebalance(CALENDAR, ndays)
    first_period = list(rule.periods_during(begin, end))[0]
    assert first_period.begin() == datetime(2012, 1, 6)
    assert first_period.end() == datetime(2012, 1, 13)

def test_nday_holidays():
    """ Tests that the nday rule falls across holidays appropriately by not countint them in the nday rule """
    begin = datetime(2011, 12, 30)
    end = datetime(2012, 1, 31)
    ndays = 5

    rule = strategy.NDayRebalance(CALENDAR, ndays)
    first_period = list(rule.periods_during(begin, end))[0]
    assert first_period.begin() == datetime(2011, 12, 30)
    assert first_period.end() == datetime(2012, 1, 9)

def test_nday_begin_end():
    """ Tests that the nday rule includes begin date as it's own first date, and end date as an end date when valid """
    begin = datetime(2012, 1, 3)
    end = datetime(2012, 2, 1)
    ndays = 5

    rule = strategy.NDayRebalance(CALENDAR, ndays)
    first_period = list(rule.periods_during(begin, end))[0]
    last_period = list(rule.periods_during(begin, end))[-1]
    assert first_period.begin() == begin
    assert last_period.end() == end

def test_annual_begin_end():
    """ Tests that the annual rule includes begin and end dates when they're valid """
    begin = datetime(2001, 1, 3)
    end = datetime(2013, 1, 3)

    rule = strategy.AnnualRebalance(CALENDAR)
    first_period = list(rule.periods_during(begin, end))[0]
    last_period = list(rule.periods_during(begin, end))[-1]
    assert first_period.begin() == begin
    assert last_period.end() == end

def test_annual_no_dates():
    """ Tests that the annual rule is empty when it includes not a full period """
    begin = datetime(2001, 1, 3)
    end = datetime(2001, 1, 4)

    rule = strategy.AnnualRebalance(CALENDAR)
    periods = list(rule.periods_during(begin, end))
    assert len(periods) == 0

def test_annual_no_dates_same_day():
    """ Tests that the annual rule is empty when it has the same begin and end """
    begin = datetime(2001, 1, 3)
    end = datetime(2001, 1, 3)

    rule = strategy.AnnualRebalance(CALENDAR)
    periods = list(rule.periods_during(begin, end))
    assert len(periods) == 0

def test_ndays_no_dates():
    """ Tests that the annual rule is empty when it includes not a full period """
    begin = datetime(2001, 1, 3)
    end = datetime(2001, 1, 4)

    rule = strategy.NDayRebalance(CALENDAR, 5)
    periods = list(rule.periods_during(begin, end))
    assert len(periods) == 0

def test_ndays_no_dates_same_day():
    """ Tests that the annual rule is empty when it has the same begin and end """
    begin = datetime(2001, 1, 3)
    end = datetime(2001, 1, 3)

    rule = strategy.NDayRebalance(CALENDAR, 5)
    periods = list(rule.periods_during(begin, end))
    assert len(periods) == 0

def test_yearly_correct_num_days():
    """ Tests that the correct number of days occur in a nday rebalance rule """
    begin = datetime(2003, 1, 3)
    end = datetime(2012, 12, 31)
    ndays = 252

    rule = strategy.AnnualRebalance(CALENDAR)
    periods = list(rule.periods_during(begin, end))
    assert all(abs(CALENDAR.trading_days_between(period.begin(), period.end()) - ndays) < 3 for period in periods)
