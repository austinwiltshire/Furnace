""" Tests classes and functions in the weathermen module """

from datetime import datetime
from furnace.test.helpers import make_default_asset_factory, is_close
from furnace.data import fcalendar
from furnace import weathermen

def test_period_average():
    """ Tests the period average weatherman regression style. This was hand confirmed """

    time_point = datetime(2012, 12, 31)
    period = 25
    calendar = fcalendar.make_fcalendar(datetime(2000, 1, 1))
    asset_factory = make_default_asset_factory(["SPY"])
    spy = asset_factory.make_asset("SPY")

    weatherman = weathermen.PeriodAverage(calendar)
    forecast = weatherman.forecast(asset_factory, time_point, period)

    assert is_close(forecast.cagr(spy), .152)

