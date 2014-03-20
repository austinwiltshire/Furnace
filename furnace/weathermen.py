""" A collection of forecasters """

class Weatherman(object):
    """ A forecaster """
    def forecast(self, asset, time_point, period):
        """ Generates a forecast of asset's future over period, at time_point """
        raise Exception("Not implemented yet")

class Forecast(object):
    """ Represents metrics from a forecaster. Currently assumes growth but can be attached to any value in the future """
    def __init__(self, asset, growth):
        self._asset = asset
        self._growth = growth

    def asset(self):
        """ Getter for asset """
        return self._asset

    def growth(self):
        """ Getter for growth """
        return self._growth

class NullForecaster(Weatherman):
    """ Returns no change for all assets """

    def forecast(self, asset, time_point, period):
        """ Returns nothing but a 0% change """
        return Forecast(asset, 1.0)

