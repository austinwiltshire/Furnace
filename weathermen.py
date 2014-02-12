class Weatherman:
    def forecast(self, asset, time_point, period):
        raise Exception("Not implemented yet")

class Forecast:
    """ Represents metrics from a forecaster. Currently assumes growth but can be attached to any value in the future """
    def __init__(self, asset, growth):
        self._asset = asset
        self._growth = growth

    def asset(self):
        return self._asset

    def growth(self):
        return self._growth

class NullForecaster(Weatherman):
    """ Returns no change for all assets """
    def forecast(self, asset, time_point, period):
        return Forecast(asset, 1.0)

