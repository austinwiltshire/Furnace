"""

Tests the asset helper class

"""

from furnace.test.helpers import make_default_asset_factory, is_close
from datetime import datetime

def test_splits():
    """ Tests that splits are handled correctly.

    There was a split issued on jun 9th 2005 on the stock IYR. Close on the 8th was 126.66, divided by 2 
    yields 63.33. The stock closed at 63.34 on the 10th, for a .0158% return 8 to june 10th

    """

    asset_factory = make_default_asset_factory(["IYR"])
    iyr = asset_factory.make_asset("IYR")

    assert is_close(iyr.between(datetime(2005, 6, 8), datetime(2005, 6, 10)).total_return(), .000158)
