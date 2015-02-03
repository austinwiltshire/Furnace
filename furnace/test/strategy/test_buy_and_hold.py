" Tests the buy and hold strategy "

from datetime import datetime
from furnace.data import fcalendar
from furnace import performance, strategy, portfolio, weathermen
from furnace.test.helpers import make_default_asset_factory, is_close, compound_growth, CALENDAR, DEFAULT_ASSET_FACTORY
import matplotlib

#TODO: look at making more specific names
def test_stocks_bonds_cagr():
    """ Tests buy and hold of two assets, spy and lqd, cagr metric from 2003-1-2 to 2012-12-31

        stocks and bonds strategy assumes static holding of 80% stocks and 20% bonds
        hand checked on august 20th """

    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    test_strategy = strategy.buy_and_hold_stocks_and_bonds(DEFAULT_ASSET_FACTORY, begin, end, CALENDAR)

    performance_ = performance.fire_furnace(test_strategy, begin, end)

    assert is_close(performance_.cagr(), 0.0666)

def test_stocks_bonds_growth_by():
    """ Tests buy and hold stocks and bonds strategy with two assets, spy and lqd, looking at growth by at multiple
        points between 2003-1-2 and 2012-12-31.

        hand checked august 20 against yahoo adj close """

    begin = datetime(2003, 1, 2)
    end = datetime(2012, 12, 31)
    test_strategy = strategy.buy_and_hold_stocks_and_bonds(DEFAULT_ASSET_FACTORY, begin, end, CALENDAR)

    performance_ = performance.fire_furnace(test_strategy, begin, end)

    assert is_close(performance_.growth_by(begin), 0.0)
    assert is_close(performance_.growth_by(datetime(2003, 2, 3)), -0.0396)
    assert is_close(performance_.growth_by(datetime(2004, 1, 2)), 0.2144)
    assert is_close(performance_.growth_by(end), 0.903)
