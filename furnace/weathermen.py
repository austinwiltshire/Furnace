""" A collection of forecasters """

import abc
import pandas as pd
import statsmodels.api as sm
from furnace.data.asset import annualized

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

#NOTE: expected that this interface will grow
#pylint: disable=R0903
class PeriodAverage(Weatherman):
    """ Returns the period stats for any particular asset """

    def __init__(self, calendar):
        self._calendar = calendar

    def forecast(self, asset_universe, time_point, period):
        """ Returns a historical based forecast """
        return PeriodAverageForecast(asset_universe, time_point, period, self._calendar)
#pylint: enable=R0903

#NOTE: expected that this interface will grow
#pylint: disable=R0903
class PeriodAverageForecast(Forecast):
    """ Forecast that uses last period's average of any asset.
    
    We forecast from period's trading days ago to today, for a total of period + 1 days
    of *value* to consider, but period days of performance since performance is judged
    off of pct_changes """

    def __init__(self, asset_factory, time_point, period, calendar):
        super(PeriodAverageForecast, self).__init__(asset_factory)
        assert time_point in calendar
        self._time_point = time_point
        self._period = period
        self._calendar = calendar

    def simple_sharpe(self, asset):
        """ Returns a period average based forecast """
        begin = self._calendar.nth_trading_day_before(self._period, self._time_point)
        end = self._time_point

#TODO: assert that asset supports begin and end dates
        return asset.between(begin, end).simple_sharpe()

    def cagr(self, asset):
        """ Returns a period average based forecast of growth"""
        begin = self._calendar.nth_trading_day_before(self._period, self._time_point)
        end = self._time_point
        return asset.between(begin, end).cagr()

#pylint: enable=R0903

class SimpleLinearForecast(Forecast):
    """ Forecast that uses last period's average of any asset.
    
    We forecast from period's trading days ago to today, for a total of period + 1 days
    of *value* to consider, but period days of performance since performance is judged
    off of pct_changes """

    def __init__(self, asset_factory, model, time_point, period, calendar):
        super(SimpleLinearForecast, self).__init__(asset_factory)
        assert time_point in calendar
        self._time_point = time_point
        self._period = period
        self._calendar = calendar
        self._model = model

    def simple_sharpe(self, asset):
        return self.cagr(asset) / self.volatility(asset)

    def volatility(self, asset):
        """ Uses a simple historical volatility """
        begin = self._calendar.nth_trading_day_before(self._period, self._time_point)
        end = self._time_point
        return asset.between(begin, end).volatility()

    def cagr(self, asset):
        """ Returns a period average based forecast of growth"""
        begin = self._calendar.nth_trading_day_before(self._period, self._time_point)
        end = self._time_point
        assert self._calendar.trading_days_between(begin, end) == 25
        return annualized(self._model.predict([1.0, asset.between(begin, end).total_return()]), 25)

class SimpleLinear(Weatherman):
    """ Returns the stats of a particular asset via a simple linear regression of 
    one month's returns """

    def __init__(self, calendar, asset):
        self._calendar = calendar
        adjusted_closes = asset._table["Adjusted Close"]
        growths = adjusted_closes.pct_change(25)
        y_x = sm.add_constant(pd.concat({'growth':growths, 'growth_lag':growths.shift(25)}, axis=1).dropna())
        model = sm.OLS(y_x["growth"], y_x[["const", "growth_lag"]])
        self._model = model.fit()

    def forecast(self, asset_universe, time_point, period):
        """ Returns a historical based forecast """
        return SimpleLinearForecast(asset_universe, self._model, time_point, period, self._calendar)

class AssetSpecific(Weatherman):
    """ Returns a specific forecasting model that depends on the asset type """
    def __init__(self, weather_team):
        self._weather_team = weather_team

    def forecast(self, asset_universe, time_point, period):
        """ Returns a historical based forecast """
        forecasts = dict([(key, forecaster.forecast(asset_universe, time_point, period))
                          for key, forecaster
                          in self._weather_team.iteritems()])
        return AssetSpecificForecast(asset_universe, forecasts)

class AssetSpecificForecast(Forecast):
    """ Returns a specific model depending on asset type """

    def __init__(self, asset_factory, forecasts):
        super(AssetSpecificForecast, self).__init__(asset_factory)
        self._forecasts = forecasts

    def simple_sharpe(self, asset):
        return self._forecasts[asset].simple_sharpe(asset)

    def volatility(self, asset):
        """ Uses a simple historical volatility """
        return self._forecasts[asset].volatility(asset)

    def cagr(self, asset):
        """ Returns a period average based forecast of growth"""
        return self._forecasts[asset].cagr(asset)
