"""
A financial calendaring module using dateutil
"""

import datetime
from dateutil.rrule import rrule, rruleset, DAILY, WEEKLY, YEARLY, MO, TU, WE, TH, FR

class FCalendar(object):
    """ A financial calendar """
    def __init__(self, daterule):
        self._daterule = daterule

    def __iter__(self):
        return iter(self._daterule)

    def nth_trading_day_after(self, nth, a_date):
        """ Finds the nth trading day after aDate.  Takes into account holidays and weekends. """

        if a_date in self._daterule: #start so i'm always on a trading day.
            trial_date = a_date
        else:
            trial_date = self._daterule.after(a_date)

        if nth == 0: #in case we actually just want the trading day we passed in
            return trial_date

        for _ in range(nth):
            trial_date = self._daterule.after(trial_date)
        return trial_date

    def nth_trading_day_before(self, nth, a_date):
        """ Finds the nth trading day before aDate.  Takes into account holidays and weekends. """
        trial_date = a_date

        if nth == 0: #in case we actually just want the trading day we passed in
            if a_date in self._daterule:
                return a_date
            else:
                return self._daterule.before(a_date)

        for _ in range(nth):
            trial_date = self._daterule.before(trial_date)
        return trial_date

def make_fcalendar(begin_date):
    """ Factory function for financial calendars """
    return FCalendar(build_trading_date_rule(begin_date))

#Move all dicts out to global scope such that they are only built once.
def build_trading_date_rule(begin_date):
    """ Helper function to build any local daily rule for iterator use.  Takes into account holidays and weekends.  Set
        begin_date to the first date available, the further back you go, the more strenuous performance. """

    days_of_mourning = {"Eisenhower":datetime.datetime(1969, 3, 31),
            "MartinLutherKing":datetime.datetime(1968, 4, 9),
            "Truman":datetime.datetime(1972, 12, 28),
            "JFK":datetime.datetime(1963, 11, 25),
            "LBJ":datetime.datetime(1973, 1, 25),
            "Nixon":datetime.datetime(1994, 4, 27),
            "Reagan":datetime.datetime(2004, 6, 11),
            "Ford":datetime.datetime(2007, 1, 2)}

    acts_of_god = {"SnowDay":datetime.datetime(1969, 2, 10), #apparently horrible weather and snow.
            "NewYorkCityBlackout":datetime.datetime(1977, 7, 14),
            "HurricaneGloria":datetime.datetime(1985, 9, 27),
            "HurricaneSandy1":datetime.datetime(2012, 10, 29),
            "HurricaneSandy2":datetime.datetime(2012, 10, 30)}

    acts_of_war = {"WorldTradeCenter1":datetime.datetime(2001, 9, 11),
            "WorldTradeCenter2":datetime.datetime(2001, 9, 12),
            "WorldTradeCenter3":datetime.datetime(2001, 9, 13),
            "WorldTradeCenter4":datetime.datetime(2001, 9, 14)}

    paper_crisis_additions = {"LincolnsBirthday":datetime.datetime(1968, 2, 12),
            "DayAfterIndependenceDay":datetime.datetime(1968, 7, 5),
            "VeteransDay":datetime.datetime(1968, 11, 11)}

    one_small_step_for_man = {"MoonLanding":datetime.datetime(1969, 7, 21)} # first lunar landing

    exception_dates = {}
    exception_dates.update(days_of_mourning)
    exception_dates.update(acts_of_god)
    exception_dates.update(acts_of_war)
    exception_dates.update(paper_crisis_additions)
    exception_dates.update(one_small_step_for_man)

    #check out : www.chronos-st.org/NYSE_Observed_Holidays-1885-Present.html
    holidays = {"PaperCrisis":rrule(WEEKLY, bymonth=(6, 7, 8, 9, 10, 11, 12), byweekday=(WE),
                                    dtstart=datetime.datetime(1968, 6, 6), until=datetime.datetime(1969, 1, 1)),
            "ElectionDayEveryYear":rrule(YEARLY, bymonth=11, bymonthday=(2, 3, 4, 5, 6, 7, 8), byweekday=(TU),
                                         dtstart=begin_date, until=datetime.datetime(1969, 1, 1)),
            "ElectionDayPresidential":rrule(YEARLY, bymonth=11, bymonthday=(2, 3, 4, 5, 6, 7, 8), byweekday=(TU),
                                            interval=4, dtstart=datetime.datetime(1972, 1, 1),
                                            until=datetime.datetime(1984, 1, 1)),
            "WashingtonsBirthdayWeek":rrule(YEARLY, bymonthday=22, bymonth=2, byweekday=(MO, TU, WE, TH, FR),
                                            dtstart=begin_date, until=datetime.datetime(1971, 1, 1)),
            "WashingtonsBirthdaySun":rrule(YEARLY, bymonthday=23, bymonth=2, byweekday=(MO), dtstart=begin_date,
                                           until=datetime.datetime(1971, 1, 1)),
            "WashingtonsBirthdaySat":rrule(YEARLY, bymonthday=21, bymonth=2, byweekday=(FR), dtstart=begin_date,
                                           until=datetime.datetime(1971, 1, 1)),
            "OldMemorialDayWeek":rrule(YEARLY, bymonthday=30, bymonth=5, byweekday=(MO, TU, WE, TH, FR),
                                       dtstart=begin_date, until=datetime.datetime(1970, 1, 1)),
            "OldMemorialDaySun":rrule(YEARLY, bymonthday=31, bymonth=5, byweekday=(MO), dtstart=begin_date,
                                      until=datetime.datetime(1970, 1, 1)),
            "OldMemorialDaySat":rrule(YEARLY, bymonthday=29, bymonth=5, byweekday=(FR), dtstart=begin_date,
                                      until=datetime.datetime(1970, 1, 1)), #there was no memorial day in 1970
            "NewYearsDayWeek":rrule(YEARLY, bymonthday=1, bymonth=1, byweekday=(MO, TU, WE, TH, FR),
                                    dtstart=begin_date),
            "NewYearsDaySun":rrule(YEARLY, bymonthday=2, bymonth=1, byweekday=(MO), dtstart=begin_date),
            "IndependenceDayWeek":rrule(YEARLY, bymonth=7, bymonthday=(4), byweekday=(MO, TU, WE, TH, FR),
                                        dtstart=begin_date),
            "IndependenceDaySun":rrule(YEARLY, bymonth=7, bymonthday=5, byweekday=(MO), dtstart=begin_date),
            "IndependenceDaySat":rrule(YEARLY, bymonth=7, bymonthday=3, byweekday=(FR), dtstart=begin_date),
            "ChristmasWeek":rrule(YEARLY, bymonth=12, bymonthday=25, byweekday=(MO, TU, WE, TH, FR),
                                  dtstart=begin_date),
            "ChristmasSun":rrule(YEARLY, bymonth=12, bymonthday=26, byweekday=(MO), dtstart=begin_date),
            "ChristmasSat":rrule(YEARLY, bymonth=12, bymonthday=24, byweekday=(FR), dtstart=begin_date),
            "GoodFriday":rrule(YEARLY, byeaster=-2, dtstart=begin_date),
            "MartinLutherKingDay":rrule(YEARLY, bymonth=1, byweekday=MO(+3), dtstart=datetime.datetime(1998, 1, 1)),
            "PresidentsDay":rrule(YEARLY, bymonth=2, byweekday=MO(+3), dtstart=datetime.datetime(1971, 1, 1)),
            "LaborDay":rrule(YEARLY, bymonth=9, byweekday=MO(+1), dtstart=begin_date),
            "NewMemorialDay":rrule(YEARLY, bymonth=5, byweekday=MO(-1), dtstart=datetime.datetime(1971, 1, 1)),
            "ThanksgivingDay":rrule(YEARLY, bymonth=11, byweekday=TH(4), dtstart=begin_date)}

    paper_crisis_rule = rrule(WEEKLY, bymonth=(6, 7, 8, 9, 10, 11, 12), byweekday=(WE),
                            dtstart=datetime.datetime(1968, 6, 6), until=datetime.datetime(1969, 1, 1))
    paper_crisis_set = rruleset()
    paper_crisis_set.rrule(paper_crisis_rule)
    paper_crisis_set.exdate(datetime.datetime(1968, 6, 5))
    paper_crisis_set.exdate(datetime.datetime(1968, 7, 3))
    paper_crisis_set.exdate(datetime.datetime(1968, 9, 4))
    paper_crisis_set.exdate(datetime.datetime(1968, 11, 6))
    paper_crisis_set.exdate(datetime.datetime(1968, 11, 13))
    paper_crisis_set.exdate(datetime.datetime(1968, 11, 27))
    holidays["PaperCrisis"] = paper_crisis_set

    trading_dates = rruleset(cache=True)
    trading_dates.rrule(rrule(DAILY, byweekday=(MO, TU, WE, TH, FR), dtstart=begin_date))
    for holiday in holidays.values():
        trading_dates.exrule(holiday)
    for exception_date in exception_dates.values():
        trading_dates.exdate(exception_date)

    return trading_dates
