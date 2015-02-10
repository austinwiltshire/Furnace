""" A financial calendaring module using dateutil """
#NOTE: I've modified dateutil according to
#http://blog.brianbeck.com/post/22129050/speeding-up-dateutil-pythons-heapq-module-turns
#this does in fact speed things up.
#This may need to be re-looked at if i move to python 3 or other changes to the dateutil library.
#It has a new version that's 3 only

from datetime import datetime, timedelta
from dateutil.rrule import rrule, rruleset, DAILY, WEEKLY, YEARLY, MO, TU, WE, TH, FR
import bisect
from pandas import Series
import numpy

def trading_days_in_year():
    """ Constant number of trading days in a year. We use a somewhat standard 252 """
    return 252.0

#TODO: test
def first_day_after(calender, a_date):
    """ Convenience function that returns first day after a trading date """
    return calender.nth_trading_day_after(0, a_date)

#TODO: test
def first_day_before(calender, a_date):
    """ Convenience function that returns first day before a trading date """
    return calender.nth_trading_date_before(0, a_date)

class FCalendar(object):
    """ A financial calendar """
    def __init__(self, dates):
        self._dates = dates

    def __contains__(self, value):
        return numpy.datetime64(value) in self._dates.values

    def nth_trading_day_after(self, nth, a_date):
        """ Finds the nth trading day after aDate.  Takes into account holidays and weekends. """

        return self._dates[bisect.bisect_left(self._dates, a_date) + nth]

    def nth_trading_day_before(self, nth, a_date):
        """ Finds the nth trading day before aDate.  Takes into account holidays and weekends. """

        return self._dates[bisect.bisect_right(self._dates, a_date) - (nth + 1)]

    def number_trading_days_between(self, begin, end):
        """ Returns the number of trading days between begin and end, exclusive of begin inclusive of end """
        return len(self._dates[self._dates > begin][self._dates <= end])

    #TODO: test
    def every_nth_between(self, begin, end, ndays):
        """ Iteration helper that gives every nth trading day between begin and end """

        #NOTE: we add one day to ensure that if end is a trading day we count it as our last period's end
        current, end = self._dates.index[(self.nth_trading_day_after(0, begin) == self._dates) |
                                         (self.nth_trading_day_before(0, end + timedelta(1)) == self._dates)]

        #NOTE: plus 1 to ensure end is in the series
        return self._dates[current:end+1:ndays]


def make_fcalendar(begin_date):
    """ Factory function for financial calendars """
    return FCalendar(build_trading_date_rule(begin_date))

def one_off_no_trading_days():
    """ Builds set of exceptions to trading days calendar that are one time events """
    days_of_mourning = {
        "Eisenhower" : datetime(1969, 3, 31),
        "MartinLutherKing" : datetime(1968, 4, 9),
        "Truman" : datetime(1972, 12, 28),
        "JFK" : datetime(1963, 11, 25),
        "LBJ" : datetime(1973, 1, 25),
        "Nixon" : datetime(1994, 4, 27),
        "Reagan" : datetime(2004, 6, 11),
        "Ford" : datetime(2007, 1, 2)
    }
    acts_of_god = {
        "SnowDay" : datetime(1969, 2, 10), #apparently horrible weather and snow.
        "NewYorkCityBlackout" : datetime(1977, 7, 14),
        "HurricaneGloria" : datetime(1985, 9, 27),
        "HurricaneSandy1" : datetime(2012, 10, 29),
        "HurricaneSandy2" : datetime(2012, 10, 30)
    }
    acts_of_war = {
        "WorldTradeCenter1" : datetime(2001, 9, 11),
        "WorldTradeCenter2" : datetime(2001, 9, 12),
        "WorldTradeCenter3" : datetime(2001, 9, 13),
        "WorldTradeCenter4" : datetime(2001, 9, 14)
    }
    paper_crisis_additions = {
        "LincolnsBirthday" : datetime(1968, 2, 12),
        "DayAfterIndependenceDay" : datetime(1968, 7, 5),
        "VeteransDay" : datetime(1968, 11, 11)
    }
    one_small_step_for_man = {"MoonLanding" : datetime(1969, 7, 21)} # first lunar landing

    exception_dates = {}
    exception_dates.update(days_of_mourning)
    exception_dates.update(acts_of_god)
    exception_dates.update(acts_of_war)
    exception_dates.update(paper_crisis_additions)
    exception_dates.update(one_small_step_for_man)
    return exception_dates

def recurrant_no_trading_days(begin_date, end_date):
    """ Helper function to construct an FCalendar, returns rrule set of all recurrant no-trade days between
    begin date and end date """
    #NOTE: check out : www.chronos-st.org/NYSE_Observed_Holidays-1885-Present.html

    def yearly(**kwargs):
        """ Helper method that builds a yearly rrule """
        return rrule(YEARLY, **kwargs)

    def recurrant_religious(begin_date, end_date):
        """ Helper function that to build an FCalendar, returns rrules set of all recurrant religious holidays on which
        no trading happens between begin_date and end_date) """
        christmas_week = yearly(
            bymonth=12,
            bymonthday=25,
            byweekday=(MO, TU, WE, TH, FR),
            dtstart=begin_date,
            until=end_date
        )
        christmas_sun = yearly(
            bymonth=12,
            bymonthday=26,
            byweekday=(MO),
            dtstart=begin_date,
            until=end_date
        )
        christmas_sat = yearly(
            bymonth=12,
            bymonthday=24,
            byweekday=(FR),
            dtstart=begin_date,
            until=end_date
        )
        good_friday = yearly(
            byeaster=-2,
            dtstart=begin_date,
            until=end_date
        )
        return [
            christmas_week,
            christmas_sun,
            christmas_sat,
            good_friday,
        ]

    def paper_crisis():
        """ Helper method to build the paper crisis one off no trading rule """
        paper_crisis_rule = rrule(
            WEEKLY,
            bymonth=(6, 7, 8, 9, 10, 11, 12),
            byweekday=(WE),
            dtstart=datetime(1968, 6, 6),
            until=datetime(1969, 1, 1)
        )
        paper_crisis_set = rruleset()
        paper_crisis_set.rrule(paper_crisis_rule)
        paper_crisis_set.exdate(datetime(1968, 6, 5))
        paper_crisis_set.exdate(datetime(1968, 7, 3))
        paper_crisis_set.exdate(datetime(1968, 9, 4))
        paper_crisis_set.exdate(datetime(1968, 11, 6))
        paper_crisis_set.exdate(datetime(1968, 11, 13))
        paper_crisis_set.exdate(datetime(1968, 11, 27))
        return [paper_crisis_set]

    def election_day(begin_date):
        """ Builds election day no trade rule """
        election_day_every_year = yearly(
            bymonth=11,
            bymonthday=(2, 3, 4, 5, 6, 7, 8),
            byweekday=(TU),
            dtstart=begin_date,
            until=datetime(1969, 1, 1)
        )
        election_day_presidential = yearly(
            bymonth=11,
            bymonthday=(2, 3, 4, 5, 6, 7, 8),
            byweekday=(TU),
            interval=4,
            dtstart=datetime(1972, 1, 1),
            until=datetime(1984, 1, 1)
        )
        return [election_day_every_year, election_day_presidential]

    def washingtons_birthday(begin_date):
        """ No trading occured on washington's birthday before 1971 """
        washingtons_birthday_week = yearly(
            bymonthday=22,
            bymonth=2,
            byweekday=(MO, TU, WE, TH, FR),
            dtstart=begin_date,
            until=datetime(1971, 1, 1)
        )
        washingtons_birthday_sun = yearly(
            bymonthday=23,
            bymonth=2,
            byweekday=(MO),
            dtstart=begin_date,
            until=datetime(1971, 1, 1)
        )
        washingtons_birthday_sat = yearly(
            bymonthday=21,
            bymonth=2,
            byweekday=(FR),
            dtstart=begin_date,
            until=datetime(1971, 1, 1)
        )
        return [washingtons_birthday_week, washingtons_birthday_sun, washingtons_birthday_sat]

    def old_memorial_day(begin_date):
        """ No trading occured on the last trading day in may before 1970 """
        old_memorial_day_week = yearly(
            bymonthday=30,
            bymonth=5,
            byweekday=(MO, TU, WE, TH, FR),
            dtstart=begin_date,
            until=datetime(1970, 1, 1)
        )
        old_memorial_day_sun = yearly(
            bymonthday=31,
            bymonth=5,
            byweekday=(MO),
            dtstart=begin_date,
            until=datetime(1970, 1, 1)
        )
        old_memorial_day_sat = yearly(
            bymonthday=29,
            bymonth=5,
            byweekday=(FR),
            dtstart=begin_date,
            until=datetime(1970, 1, 1)
        ) #there was no memorial day in 1970
        return [old_memorial_day_week, old_memorial_day_sun, old_memorial_day_sat]

    def new_years_day(begin_date, end_date):
        """ No trading on new years day if it's during the week or sunday """
        new_years_day_week = yearly(
            bymonthday=1,
            bymonth=1,
            byweekday=(MO, TU, WE, TH, FR),
            dtstart=begin_date,
            until=end_date
        )
        new_years_day_sun = yearly(
            bymonthday=2,
            bymonth=1,
            byweekday=(MO),
            dtstart=begin_date
        )
        return [new_years_day_week, new_years_day_sun]

    def independence_day(begin_date, end_date):
        """ No trading on the trading day nearest to july 4th """
        independence_day_week = yearly(
            bymonth=7,
            bymonthday=(4),
            byweekday=(MO, TU, WE, TH, FR),
            dtstart=begin_date,
            until=end_date
        )
        independence_day_sun = yearly(
            bymonth=7,
            bymonthday=5,
            byweekday=(MO),
            dtstart=begin_date,
            until=end_date
        )
        independence_day_sat = yearly(
            bymonth=7,
            bymonthday=3,
            byweekday=(FR),
            dtstart=begin_date,
            until=end_date
        )
        return [independence_day_week, independence_day_sun, independence_day_sat]

    def federal_holidays(begin_date, end_date):
        """ No trading on MLK, presidents day, labor day, memorial day or thanksgiving day """
        martin_luther_king_day = yearly(
            bymonth=1,
            byweekday=MO(+3),
            dtstart=datetime(1998, 1, 1),
            until=end_date
        )
        presidents_day = yearly(
            bymonth=2,
            byweekday=MO(+3),
            dtstart=datetime(1971, 1, 1),
            until=end_date
        )
        labor_day = yearly(
            bymonth=9,
            byweekday=MO(+1),
            dtstart=begin_date,
            until=end_date
        )
        new_memorial_day = yearly(
            bymonth=5,
            byweekday=MO(-1),
            dtstart=datetime(1971, 1, 1),
            until=end_date
        )
        thanksgiving_day = yearly(
            bymonth=11,
            byweekday=TH(4),
            dtstart=begin_date,
            until=end_date
        )
        return [
            martin_luther_king_day,
            presidents_day,
            labor_day,
            new_memorial_day,
            thanksgiving_day
        ]

    holidays = (
        paper_crisis() +
        recurrant_religious(begin_date, end_date) +
        federal_holidays(begin_date, end_date) +
        independence_day(begin_date, end_date) +
        new_years_day(begin_date, end_date) +
        old_memorial_day(begin_date) +
        washingtons_birthday(begin_date) +
        election_day(begin_date)
    )
    trading_dates = rruleset(cache=True)
    for holiday in holidays:
        trading_dates.exrule(holiday)
    return trading_dates

#NOTE: A potential optimization was considered of moving all rrules out to class or global scope to
#prevent reinitialization. This is currently impossible since those rules require begin and end date
#to be defined in many cases
def build_trading_date_rule(begin_date, end_date=None):
    """ Helper function to build any local daily rule for iterator use.  Takes into account holidays and weekends.  Set
        begin_date to the first date available, the further back you go, the more strenuous performance. """

    if not end_date:
        end_date = datetime.today()

    exception_dates = one_off_no_trading_days()
    trading_dates = recurrant_no_trading_days(begin_date, end_date)
    trading_dates.rrule(rrule(
        DAILY,
        byweekday=(MO, TU, WE, TH, FR),
        dtstart=begin_date,
        until=end_date)
    )
    for exception_date in exception_dates.values():
        trading_dates.exdate(exception_date)

    return Series(list(trading_dates))
