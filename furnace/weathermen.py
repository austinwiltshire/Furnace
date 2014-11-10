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
    def simple_sharpe(self, asset):
        """ Getter for the simple sharpe """
        pass
#pylint: enable=R0922,R0903

#NOTE: invariably will add forecasts for volatility at least
#pylint: disable=R0903
#TODO: this should be a class held by nullforecaster as an inner class
class NullForecast(Forecast):
    """ Simply returns some default value for all symbols """

    def __init__(self, asset_universe, simple_sharpe):
        super(NullForecast, self).__init__(asset_universe)
        self._simple_sharpe = simple_sharpe

    def simple_sharpe(self, _):
        """ Returns a default growth value """
        return self._simple_sharpe
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

#NOTE: expected that this interface will grow
#pylint: disable=R0903
class HistoricalAverageForecast(Forecast):
    """ Forecast simply returns the historical average of any asset """

    def __init__(self, asset_factory):
        super(HistoricalAverageForecast, self).__init__(asset_factory)

    def simple_sharpe(self, asset):
        return asset.simple_sharpe()
#pylint: enable=R0903

#NOTE: expected that this interface will grow
#pylint: disable=R0903
class HistoricalAverage(Weatherman):
    """ Returns the historical stats for any particular asset """

    def forecast(self, asset_universe, time_point, period):
        """ Returns a historical based forecast """
        return HistoricalAverageForecast(asset_universe)
#pylint: enable=R0903
