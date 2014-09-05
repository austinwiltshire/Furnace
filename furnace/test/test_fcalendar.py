"""
Test the fcalendar module
"""

import unittest
from furnace.data import fcalendar, yahoo
import datetime
import itertools
import os.path
import pickle

#pylint: disable=R0904
class TestFcalendar(unittest.TestCase):
    """ Test various dates in the financial calendaring system """

    def setUp(self):
        """ Initialize fixture """
        self.trading_dates = fcalendar.build_trading_date_rule(datetime.datetime(2001, 1, 1))

    def test_weekends(self):
        """ Test that weekends don't fall in trading dates """

        self.assertFalse(datetime.datetime(2002, 3, 9) in self.trading_dates)
        self.assertFalse(datetime.datetime(2002, 3, 10) in self.trading_dates)

    def test_holidays(self):
        """ Test that some holidays aren't treated as trading dates """

        self.assertFalse(datetime.datetime(2003, 12, 25) in self.trading_dates)
        self.assertFalse(datetime.datetime(2003, 5, 26) in self.trading_dates) # memorial day

    def test_weekdays(self):
        """ Test that normal weekdays are trading dates """

        self.assertTrue(datetime.datetime(2004, 5, 21) in self.trading_dates)
        self.assertTrue(datetime.datetime(2004, 5, 17) in self.trading_dates)
        self.assertTrue(datetime.datetime(2004, 5, 18) in self.trading_dates)
        self.assertTrue(datetime.datetime(2004, 5, 19) in self.trading_dates)
        self.assertTrue(datetime.datetime(2004, 5, 20) in self.trading_dates)
#pylint: enable=R0904

#pylint: disable=R0904
class TestFcalendarHelpers(unittest.TestCase):
    """ Test the before and after helpers """

    def test_after(self):
        """ Test the after logic """

        date = datetime.datetime
        calendar = fcalendar.make_fcalendar(datetime.datetime(2000, 1, 1))

        self.assertTrue(calendar.nth_trading_day_after(3, date(2005, 6, 13)) == date(2005, 6, 16))
        self.assertTrue(calendar.nth_trading_day_after(0, date(2005, 6, 13)) == date(2005, 6, 13))
        self.assertTrue(calendar.nth_trading_day_after(0, date(2005, 6, 18)) == date(2005, 6, 20))

    def test_before(self):
        """ Test the after logic """

        date = datetime.datetime
        calendar = fcalendar.make_fcalendar(datetime.datetime(2000, 1, 1))

        #july forth is this week
        self.assertTrue(calendar.nth_trading_day_before(3, date(2006, 7, 7)) == date(2006, 7, 3))
        self.assertTrue(calendar.nth_trading_day_before(0, date(2006, 7, 7)) == date(2006, 7, 7))
        self.assertTrue(calendar.nth_trading_day_before(0, date(2006, 7, 8)) == date(2006, 7, 7))
#pylint: enable=R0904

#pylint: disable=R0904
#NOTE: too many public methods
class TestFCalendarRange(unittest.TestCase):
    """ Test that the range of the calendar is correct """

    def test_range(self):
        """ Tests that the range of the calendar covers the same range as the data """
        begin_date = datetime.datetime(2000, 1, 1)
        end_date = datetime.datetime.today()

        if os.path.isfile("spy_price_cache_" + str(datetime.date.today()) + ".csv"):
            dates_available = pickle.load(open("spy_price_cache_" + str(datetime.date.today()) + ".csv", "r"))
        else:
            prices_available = yahoo.webload_symbol_price("SPY", begin_date, end_date)
            dates_available = set(timestamp.to_pydatetime() for timestamp in prices_available.index.tolist())
            pickle.dump(dates_available, open("spy_price_cache_" + str(datetime.date.today()) + ".csv", "w"))

        calendar = fcalendar.make_fcalendar(begin_date)
        dates_expected = set([day for day in itertools.takewhile(lambda d: d <= end_date, [x for x in calendar])])

#        import IPython
#        IPython.embed()
        dates_misaligned = dates_available.symmetric_difference(dates_expected)

        self.assertEqual(len(dates_misaligned), 0)
#pylint: enable=R0904
