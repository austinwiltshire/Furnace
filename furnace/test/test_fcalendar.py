"""
Test the fcalendar module
"""

from furnace.data import fcalendar, yahoo
from furnace.test.helpers import CALENDAR
import datetime
import itertools
import os.path
import pickle
from numpy import datetime64

TRADING_DATES = fcalendar.build_trading_date_rule(datetime.datetime(2001, 1, 1))

def test_weekends():
    """ Test that weekends don't fall in trading dates """

    assert not datetime.datetime(2002, 3, 9) in TRADING_DATES
    assert not datetime.datetime(2002, 3, 10) in TRADING_DATES

def test_holidays():
    """ Test that some holidays aren't treated as trading dates """

    assert not datetime.datetime(2003, 12, 25) in TRADING_DATES
    assert not datetime.datetime(2003, 5, 26) in TRADING_DATES # memorial day

def test_weekdays():
    """ Test that normal weekdays are trading dates """

    def make_date(year, month, day):
        """ Helper to create numpy datetimes """
        return datetime64(datetime.datetime(year, month, day))

    assert make_date(2004, 5, 21) in TRADING_DATES.values
    assert make_date(2004, 5, 17) in TRADING_DATES.values
    assert make_date(2004, 5, 18) in TRADING_DATES.values
    assert make_date(2004, 5, 19) in TRADING_DATES.values
    assert make_date(2004, 5, 20) in TRADING_DATES.values

def test_after():
    """ Test the after logic """
    date = datetime.datetime

    assert CALENDAR.nth_trading_day_after(3, date(2005, 6, 13)) == date(2005, 6, 16)
    assert CALENDAR.nth_trading_day_after(0, date(2005, 6, 13)) == date(2005, 6, 13)
    assert CALENDAR.nth_trading_day_after(0, date(2005, 6, 18)) == date(2005, 6, 20)

def test_before():
    """ Test the before logic """
    date = datetime.datetime

    #july forth is this week
    assert CALENDAR.nth_trading_day_before(3, date(2006, 7, 7)) == date(2006, 7, 3)
    assert CALENDAR.nth_trading_day_before(0, date(2006, 7, 7)) == date(2006, 7, 7)
    assert CALENDAR.nth_trading_day_before(0, date(2006, 7, 8)) == date(2006, 7, 7)

def test_range():
    """ Tests that the range of the calendar covers the same range as the data """
    begin_date = datetime.datetime(2000, 1, 1)
    end_date = datetime.datetime.today()

    if os.path.isfile("spy_price_cache_" + str(datetime.date.today()) + ".csv"):
        dates_available = pickle.load(open("spy_price_cache_" + str(datetime.date.today()) + ".csv", "r"))
    else:
        prices_available = yahoo.webload_symbol_price("SPY", begin_date, end_date)
        dates_available = set(timestamp.to_pydatetime() for timestamp in prices_available.index.tolist())
        pickle.dump(dates_available, open("spy_price_cache_" + str(datetime.date.today()) + ".csv", "w"))

    dates_expected = set([day for day in itertools.takewhile(
        lambda d: d <= end_date,
        CALENDAR.every_nth_between(begin_date, end_date, 1)
    )])

    dates_misaligned = dates_available.symmetric_difference(dates_expected)

    assert len(dates_misaligned) == 0
