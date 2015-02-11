""" Tests classes and functions in the weathermen module """

from datetime import datetime
from furnace.test.helpers import is_close, CALENDAR, DEFAULT_ASSET_FACTORY
from furnace import weathermen

def test_period_average():
    """ Tests the period average weatherman regression style. This was hand confirmed """

    time_point = datetime(2012, 12, 31)
    period = 25
    spy = DEFAULT_ASSET_FACTORY.make_asset("SPY")

    weatherman = weathermen.period_average(CALENDAR)
    forecast = weatherman(DEFAULT_ASSET_FACTORY, time_point, period)

    assert is_close(forecast.cagr(spy), .152)

def test_simple_autocorr():
    """ Tests a simple autocorrelation forecaster. Hand checked the actual prediction, but simply sanity
    checked behavior of the model itself """

    time_point = datetime(2012, 12, 31)
    period = 25
    spy = DEFAULT_ASSET_FACTORY.make_asset("SPY")

    test_weatherman = weathermen.simple_linear(CALENDAR, spy)
    forecast = test_weatherman(DEFAULT_ASSET_FACTORY, time_point, period)

    assert is_close(forecast.cagr(spy), 0.0958)

def test_asset_specific():
    """ Tests the combination of asset forecasts using the AssetSpecific weatherman
    Did a sanity check on the returns for the lqd forecast and uup """

    time_point = datetime(2012, 12, 31)
    period = 25
    spy = DEFAULT_ASSET_FACTORY.make_asset("SPY")
    lqd = DEFAULT_ASSET_FACTORY.make_asset("LQD")
    uup = DEFAULT_ASSET_FACTORY.make_asset("UUP")

    spy_weatherman = weathermen.simple_linear(CALENDAR, spy)

    #The simple linear forecaster is actually really bad for lqd
    lqd_weatherman = weathermen.simple_linear(CALENDAR, lqd)
    uup_weatherman = weathermen.simple_linear(CALENDAR, uup)

    forecasts_dictionary = {spy: spy_weatherman, lqd: lqd_weatherman, uup: uup_weatherman}
    test_weatherman = weathermen.asset_specific(forecasts_dictionary)
    forecast = test_weatherman(DEFAULT_ASSET_FACTORY, time_point, period)

    assert is_close(forecast.cagr(spy), 0.09580)
    assert is_close(forecast.cagr(lqd), 0.07035)
    assert is_close(forecast.cagr(uup), 0.00251)

