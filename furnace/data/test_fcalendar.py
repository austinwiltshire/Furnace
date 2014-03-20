"""
Test the fcalendar module
"""

import unittest
from furnace.data import fcalendar
import datetime

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

class TestFcalendarHelpers(unittest.TestCase):
    """ Test the before and after helpers """

    def test_after(self):
        """ Test the after logic """

        date = datetime.datetime

        self.assertTrue(fcalendar.nth_trading_day_after(date(2005, 6, 13), 3) == date(2005, 6, 16))
        self.assertTrue(fcalendar.nth_trading_day_after(date(2005, 6, 13), 0) == date(2005, 6, 13))
        self.assertTrue(fcalendar.nth_trading_day_after(date(2005, 6, 18), 0) == date(2005, 6, 20))

    def test_before(self):
        """ Test the after logic """

        date = datetime.datetime

        #july forth is this week
        self.assertTrue(fcalendar.nth_trading_day_before(date(2006, 7, 7), 3) == date(2006, 7, 3))
        self.assertTrue(fcalendar.nth_trading_day_before(date(2006, 7, 7), 0) == date(2006, 7, 7))
        self.assertTrue(fcalendar.nth_trading_day_before(date(2006, 7, 8), 0) == date(2006, 7, 7))

if __name__ == '__main__':
    unittest.main()
