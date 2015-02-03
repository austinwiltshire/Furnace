" Tests behavior of the ndays rebalancing rule "

from datetime import datetime
from furnace import strategy
from furnace.test.helpers import CALENDAR, DEFAULT_ASSET_FACTORY

def test_count_days_abs():
    """ Test that the last day of an nday trading period falls n absolute days after beginning if there is
    nothing but valid trading days in between """
    begin = datetime(2012, 1, 3)
    end = datetime(2012, 1, 31)

    rebalanced = strategy.ndays_rebalance_single_asset(DEFAULT_ASSET_FACTORY, CALENDAR, "SPY", 2)

    periods = list(rebalanced.periods_during(begin, end))

    #the end of the first period should be 2 trading days in, starting on the 3rd, so 2012, 1, 5
    assert periods[0].begin() == datetime(2012, 1, 3)
    assert periods[0].end() == datetime(2012, 1, 5)

def test_period_size():
    """ Tests that the correct number of days occur in a nday rebalance rule """
    begin = datetime(2012, 1, 3)
    end = datetime(2012, 1, 31)
    ndays = 5

    rule = strategy.NDayRebalance(CALENDAR, ndays)
    periods = list(rule.periods_during(begin, end))
    assert all(CALENDAR.number_trading_days_between(period.begin(), period.end()) == ndays for period in periods)

def test_weekends():
    """ Tests that the nday rule falls across weekends appropritately by not counting them in the nday rule """
    begin = datetime(2012, 1, 6)
    end = datetime(2012, 1, 31)
    ndays = 5

    rule = strategy.NDayRebalance(CALENDAR, ndays)
    first_period = list(rule.periods_during(begin, end))[0]
    assert first_period.begin() == datetime(2012, 1, 6)
    assert first_period.end() == datetime(2012, 1, 13)

def test_holidays():
    """ Tests that the nday rule falls across holidays appropriately by not countint them in the nday rule """
    begin = datetime(2011, 12, 30)
    end = datetime(2012, 1, 31)
    ndays = 5

    rule = strategy.NDayRebalance(CALENDAR, ndays)
    first_period = list(rule.periods_during(begin, end))[0]
    assert first_period.begin() == datetime(2011, 12, 30)
    assert first_period.end() == datetime(2012, 1, 9)

def test_begin_end_inclusion():
    """ Tests that the nday rule includes begin date as it's own first date, and end date as an end date when valid """
    begin = datetime(2012, 1, 3)
    end = datetime(2012, 2, 1)
    ndays = 5

    rule = strategy.NDayRebalance(CALENDAR, ndays)
    first_period = list(rule.periods_during(begin, end))[0]
    last_period = list(rule.periods_during(begin, end))[-1]
    assert first_period.begin() == begin
    assert last_period.end() == end

def test_empty_period():
    """ Tests that the ndays rule is empty when it includes not a full period """
    begin = datetime(2001, 1, 3)
    end = datetime(2001, 1, 4)

    rule = strategy.NDayRebalance(CALENDAR, 5)
    periods = list(rule.periods_during(begin, end))
    assert len(periods) == 0

def test_empty_period_same_day():
    """ Tests that the annual rule is empty when it has the same begin and end """
    begin = datetime(2001, 1, 3)
    end = datetime(2001, 1, 3)

    rule = strategy.NDayRebalance(CALENDAR, 5)
    periods = list(rule.periods_during(begin, end))
    assert len(periods) == 0

def test_correct_num_days():
    """ Tests that the correct number of days occur in a nday rebalance rule """
    begin = datetime(2003, 1, 3)
    end = datetime(2012, 12, 31)
    ndays = 252

    rule = strategy.AnnualRebalance(CALENDAR)
    periods = list(rule.periods_during(begin, end))
    assert all(
        abs(CALENDAR.number_trading_days_between(period.begin(), period.end()) - ndays) < 3
        for period
        in periods
    )
