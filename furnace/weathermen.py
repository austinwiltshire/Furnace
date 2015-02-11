""" A collection of forecasters """

import abc
import pandas as pd
import statsmodels.api as sm
from furnace.data.asset import annualized

class Forecast(object):
    """ Represents metrics from a forecaster. Currently assumes growth but can be attached to any value in the
        future """
    __metaclass__ = abc.ABCMeta

    def __init__(self, asset_factory):
        self._asset_factory = asset_factory

    @abc.abstractmethod
    def simple_sharpe(self, asset):
        """ Getter for the simple sharpe """
        pass

    @abc.abstractmethod
    def cagr(self, asset):
        """ Generates a cagr estimate for the asset """
        pass

    @abc.abstractmethod
    def volatility(self, asset):
        """ Generates a volatility estimate for the asset """
        pass

def null_forecaster():
    """ A null forecaster returns canned input. Useful for testing portfolio optimizers and
    strategies that don't rely on forecasts """

    def forecast(asset_factory, dummy_time_point, dummy_period):
        """ Factory function for the null forecaster """
        return Null(asset_factory, 1.0, 1.0)
    return forecast

class Null(Forecast):
    """ Simply returns some default value for all symbols """

    def __init__(self, asset_factory, cagr, volatility):
        super(Null, self).__init__(asset_factory)
        self._cagr = cagr
        self._volatility = volatility

    #TODO: remove simple sharpe and add a helper at the module level
    def simple_sharpe(self, _):
        """ Returns a default growth value """
        return self.cagr() / self.volatility()

    def cagr(self, _):
        """ Returns the static cagr """
        return self._cagr

    def volatility(self, _):
        """ Returns the static volatility """
        return self._volatility

def historical_average():
    """ Historical average bases it's forecasts on the average of all history for an asset.
    All data we have is used to generate the average, including all of past history and all
    future we have access too, even past the date we're looking """

    def forecast(asset_factory, dummy_time_point, dummy_period):
        """ Factory function for the historical average forecaster """
        return HistoricalAverage(asset_factory)

    return forecast

class HistoricalAverage(Forecast):
    """ Forecast simply returns the historical average of any asset """

    def __init__(self, asset_factory):
        super(HistoricalAverage, self).__init__(asset_factory)

    def simple_sharpe(self, asset):
        return self.cagr(asset) / self.volatility(asset)

    def cagr(self, asset):
        return asset.cagr(asset.begin(), asset.end())

    def volatility(self, asset):
        return asset.volatility(asset.begin(), asset.end())

def period_average(calendar):
    """ Period average forecaster uses the previous period, defined by some n-trading days ago to the present
    to generate an average for growth or volatility. """

    def forecast(asset_factory, time_point, period):
        """ Factory function for the period average forecaster """
        return PeriodAverage(asset_factory, time_point, period, calendar)

    return forecast

class PeriodAverage(Forecast):
    """ Forecast that uses last period's average of any asset.
    We forecast from period's trading days ago to today, for a total of period + 1 days
    of *value* to consider, but period days of performance since performance is judged
    off of pct_changes """

    def __init__(self, asset_factory, time_point, period, calendar):
        super(PeriodAverage, self).__init__(asset_factory)
        assert time_point in calendar
        self._time_point = time_point
        self._period = period
        self._calendar = calendar

    def simple_sharpe(self, asset):
        """ Returns a period average based forecast """
        return self.cagr(asset) / self.volatility(asset)

    def cagr(self, asset):
        """ Returns a period average based forecast of growth"""
        return asset.cagr(self._begin(), self._end())

    def volatility(self, asset):
        """ Returns a period average based forecast of volatility """
        return asset.volatility(self._begin(), self._end())

    def _begin(self):
        """ Gets this period forecasts beginning of the period """
        return self._calendar.nth_trading_day_before(self._period, self._time_point)

    def _end(self):
        """ End of this period """
        return self._time_point

def simple_linear(calendar, asset):
    """ Creates a simple linear predictor of a single asset """

    adjusted_closes = asset._table["Adjusted Close"]
    growths = adjusted_closes.pct_change(25)
    y_x = sm.add_constant(pd.concat({'growth':growths, 'growth_lag':growths.shift(25)}, axis=1).dropna())
    model = sm.OLS(y_x["growth"], y_x[["const", "growth_lag"]])
    fit = model.fit()

    def make_forecast(asset_factory, time_point, period):
        """ Returns the forecast for a particular time period """
        return SimpleLinear(asset_factory, fit, time_point, period, calendar)

    return make_forecast

class SimpleLinear(Forecast):
    """ Forecast that uses last period's average of any asset.
    We forecast from period's trading days ago to today, for a total of period + 1 days
    of *value* to consider, but period days of performance since performance is judged
    off of pct_changes """

    def __init__(self, asset_factory, model, time_point, period, calendar):
        super(SimpleLinear, self).__init__(asset_factory)
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
        return asset.volatility(begin, end)

    def cagr(self, asset):
        """ Returns a period average based forecast of growth"""
        begin = self._calendar.nth_trading_day_before(self._period, self._time_point)
        end = self._time_point
        assert self._calendar.number_trading_days_between(begin, end) == 25
        return annualized(self._model.predict([1.0, asset.total_return(begin, end)]), 25)

class AssetSpecific(Forecast):
    """ Returns a specific model depending on asset type """

    def __init__(self, asset_factory, forecasts):
        super(AssetSpecific, self).__init__(asset_factory)
        self._forecasts = forecasts

    def simple_sharpe(self, asset):
        return self._forecasts[asset].simple_sharpe(asset)

    def volatility(self, asset):
        """ Uses a simple historical volatility """
        return self._forecasts[asset].volatility(asset)

    def cagr(self, asset):
        """ Returns a period average based forecast of growth"""
        return self._forecasts[asset].cagr(asset)

def asset_specific(weather_team):
    """ Asset specific forecaster is merely a wrapper around other forecasters that are then
    looked up on a asset symbol name basis. So for instance LQD and SPY can use different models """

    def forecast(asset_factory, time_point, period):
        """ Returns a forecaster that wraps other forecasters based on asset symbol lookup"""
        forecasts = dict([(key, forecaster(asset_factory, time_point, period))
                          for key, forecaster
                          in weather_team.iteritems()])

        return AssetSpecific(asset_factory, forecasts)

    return forecast

