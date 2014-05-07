""" A collection of forecasters """

import abc

#NOTE: expected that this interface will grow and more people will inherit
#pylint: disable=R0903
#pylint: disable=R0922
class Weatherman(object):
    """ A forecaster """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def forecast(self, asset_universe, time_point, period):
        """ Generates a forecast of asset's future over period, at time_point """
        pass
#pylint: enable=R0903
#pylint: enable=R0922

#NOTE: invariably will add different forecasts using different forecasting models
#pylint: disable=R0922,R0903
class Forecast(object):
    """ Represents metrics from a forecaster. Currently assumes growth but can be attached to any value in the
        future """
    __metaclass__ = abc.ABCMeta

    def __init__(self, asset_universe):
        self._asset_universe = asset_universe

    @abc.abstractmethod
    def growth(self, symbol):
        """ Getter for growth """
        pass
#pylint: enable=R0922,R0903

#NOTE: invariably will add forecasts for volatility at least
#pylint: disable=R0903
class NullForecast(Forecast):
    """ Simply returns some default value for all symbols """

    def __init__(self, asset_universe, growth):
        super(NullForecast, self).__init__(asset_universe)
        self._growth = growth

    def growth(self, symbol):
        """ Returns a default growth value """
        return self._growth
#pylint: enable=R0903

#NOTE: expected that this interface will grow
#pylint: disable=R0903
class NullForecaster(Weatherman):
    """ Returns no change for all assets """

#NOTE: do not add asset universe as an init param - strategy ensures that the same asset universe is passed in to
#portfolio optimizer and weatherman
    def forecast(self, asset_universe, time_point, period):
        """ Returns nothing but a 0% change """
        return NullForecast(asset_universe, 1.0)
#pylint: enable=R0903
