" Tests behavior of the annual rebalancing rule "

from datetime import datetime
from furnace import strategy
from furnace.test.helpers import is_close, CALENDAR, DEFAULT_ASSET_FACTORY

def test_perf_eq_buy_and_hold():
    """ Tests that a annual rebalanced strategy of one stock equals a buy and hold strategy of the same """

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

    reference_performance = reference.performance_during(begin, end)
    rebalanced_performance = rebalanced.performance_during(begin, end)

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

def test_begin_end():
    """ Tests that the annual rule includes begin and end dates when they're valid """
    begin = datetime(2001, 1, 3)
    end = datetime(2013, 1, 3)

    rule = strategy.AnnualRebalance(CALENDAR)
    first_period = list(rule.periods_during(begin, end))[0]
    last_period = list(rule.periods_during(begin, end))[-1]
    assert first_period.begin() == begin
    assert last_period.end() == end

def test_empty_when_less_than_year():
    """ Tests that the annual rule is empty when it includes not a full period """
    begin = datetime(2001, 1, 3)
    end = datetime(2001, 1, 4)

    rule = strategy.AnnualRebalance(CALENDAR)
    periods = list(rule.periods_during(begin, end))
    assert len(periods) == 0

def test_empty_when_zero_days():
    """ Tests that the annual rule is empty when it has the same begin and end """
    begin = datetime(2001, 1, 3)
    end = datetime(2001, 1, 3)

    rule = strategy.AnnualRebalance(CALENDAR)
    periods = list(rule.periods_during(begin, end))
    assert len(periods) == 0
