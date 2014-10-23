""" Helper functions for testing """

import numpy
from furnace.data import fcalendar, yahoo, asset
from datetime import datetime

def is_close(val, other_val):
    """ Checks two floating points are 'close enough'.

        A relative difference of 3 usually is 'close enough' given that we check against yahoo data a lot """
    return numpy.isclose(val, other_val, rtol=1e-03)

def make_default_asset_factory(symbols):
    """ Helper method returns an asset factory for a list of symbols with a calendar starting at 2000-1-1 """

    calendar = fcalendar.make_fcalendar(datetime(2000, 1, 1))
    data_cache = yahoo.load_pandas()
    return asset.AssetUniverse(symbols, data_cache, calendar)

def compound_growth(*returns):
    """ Returns the compound return of the associated individual returns """
    return (1.0 + numpy.array(returns)).prod() - 1.0
