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

def test_simple_autocorr():
    """ Tests a simple autocorrelation forecaster. Hand checked the actual prediction, but simply sanity
    checked behavior of the model itself """

    time_point = datetime(2012, 12, 31)
    period = 25
    calendar = fcalendar.make_fcalendar(datetime(2000, 1, 1))
    asset_factory = make_default_asset_factory(["SPY"])
    spy = asset_factory.make_asset("SPY")

    test_weatherman = weathermen.SimpleLinear(calendar, spy)
    forecast = test_weatherman.forecast(asset_factory, time_point, period)

    assert is_close(forecast.cagr(spy), 0.0958)

def test_asset_specific():
    """ Tests the combination of asset forecasts using the AssetSpecific weatherman
    Did a sanity check on the returns for the lqd forecast and uup """

    time_point = datetime(2012, 12, 31)
    period = 25
    calendar = fcalendar.make_fcalendar(datetime(2000, 1, 1))
    asset_factory = make_default_asset_factory(["SPY", "LQD", "UUP"])
    spy = asset_factory.make_asset("SPY")
    lqd = asset_factory.make_asset("LQD")
    uup = asset_factory.make_asset("UUP")

    spy_weatherman = weathermen.SimpleLinear(calendar, spy)

    #The simple linear forecaster is actually really bad for lqd
    lqd_weatherman = weathermen.SimpleLinear(calendar, lqd)
    uup_weatherman = weathermen.SimpleLinear(calendar, uup)

    forecasts_dictionary = {spy: spy_weatherman, lqd: lqd_weatherman, uup: uup_weatherman}
    test_weatherman = weathermen.AssetSpecific(forecasts_dictionary)
    forecast = test_weatherman.forecast(asset_factory, time_point, period)

    assert is_close(forecast.cagr(spy), 0.09580)
    assert is_close(forecast.cagr(lqd), 0.07035)
    assert is_close(forecast.cagr(uup), 0.00251)

