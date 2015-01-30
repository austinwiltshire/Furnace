"""

Tests the asset helper class

"""

from furnace.test.helpers import make_default_asset_factory, is_close, DEFAULT_ASSET_FACTORY
from datetime import datetime
from furnace.data.asset import adjust_period, annualized

def test_splits():
    """ Tests that splits are handled correctly.

    There was a split issued on jun 9th 2005 on the stock IYR. Close on the 8th was 126.66, divided by 2 
    yields 63.33. The stock closed at 63.34 on the 10th, for a .0158% return 8 to june 10th

    """

    iyr = DEFAULT_ASSET_FACTORY.make_asset("IYR")

    assert is_close(iyr.total_return(datetime(2005, 6, 8), datetime(2005, 6, 10)), .000158)

def test_adjust_period():
    """ Tests that period arithmatic is correct """

    assert is_close(adjust_period(0.055, 20, 252), annualized(.055, 20))
    assert is_close(adjust_period(0.6, 20, 1), 0.02378)
