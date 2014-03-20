""" Tests strategies and tests known metrics. REGRESSION style tests simply test that known outputs from the models
    do not vary with changes - there is no guarantee that their original values are correct. In many cases, a
    combination of audit (print outputs and calculations, hand check a sample), code review or back of the envelope
    calculations have been used to sanity check the outputs of regression style tests. """

import unittest
import datetime
from data import asset, yahoo
import performance
import strategy
import numpy

class TestBuyAndHold(unittest.TestCase):
    """ Integration test of trading strategies """

    def setUp(self):
        """ Initialize fixture """
        self.furnace = performance.Furnace()
        self.data_cache = yahoo.load() 
        self.asset_factory = asset.AssetFactory(self.data_cache)

    def test_buy_and_hold(self):
        """ Tests the simplest buy and hold strategy """
        #TODO: move "data cache" into the data.py
        #NOTE: data_cache will be eager loaded (current design, anyway)

        begin = datetime.date(2001, 1, 2)
        end = datetime.date(2012, 12, 31)
        performance_ = self.furnace.fire(strategy.BuyAndHoldStocks(self.asset_factory, begin), begin, end)
        self.assertTrue(numpy.isclose(performance_.CAGR(), 1.02763283748, 1e-11, 1e-11))

    def test_index_index(self):
        """ Regression Tests indexing a strategy with a base index """

        #TODO: should i grab begin and end from the data cache?
        begin = datetime.date(2001, 1, 2)
        end = datetime.date(2012, 12, 31)
        strat = strategy.BuyAndHoldStocks(self.asset_factory, datetime.date(2001, 1, 2))
        performance_ = self.furnace.fire(strat, begin, end)

        self.assertTrue(numpy.isclose(performance_.index_on(datetime.date(2001, 1, 2), 100), 100))
        self.assertTrue(numpy.isclose(performance_.index_on(datetime.date(2001, 2, 1), 100), 107.3378))
        self.assertTrue(numpy.isclose(performance_.index_on(datetime.date(2002, 1, 2), 100), 90.881805))
        self.assertTrue(numpy.isclose(performance_.index_on(datetime.date(2012, 12, 31), 100), 138.7037))

class TestBondsAndStocks(unittest.TestCase):
    """ Test various metrics on a buy and hold portfolio that is 90% stocks and 10% bonds """

    def setUp(self):
        """ Initialize fixture """
        self.furnace = performance.Furnace()
        self.data_cache = yahoo.load()
        self.asset_factory = asset.AssetFactory(self.data_cache)

    def test_buy_and_hold(self):
        """ REGRESSION tests mixed portfolio """
        #TODO: move "data cache" into the data.py
        #NOTE: data_cache will be eager loaded (current design, anyway)
        begin = datetime.date(2003, 1, 2)
        end = datetime.date(2012, 12, 31)
        performance_ = self.furnace.fire(strategy.BuyAndHoldStocksAndBonds(self.asset_factory, begin), begin, end)

        self.assertTrue(numpy.isclose(performance_.CAGR(), 1.06607730908, 1e-11, 1e-11))

    def test_index_index(self):
        """ REGRESSION tests mixed portfolio """
        #TODO: should i grab begin and end from the data cache?
        begin = datetime.date(2003, 1, 2)
        end = datetime.date(2012, 12, 31)
        strat = strategy.BuyAndHoldStocksAndBonds(self.asset_factory, datetime.date(2003, 1, 2))
        performance_ = self.furnace.fire(strat, begin, end)

        #TODO: refactor the commonality out of tehse tests
        #TODO: this check below should always be true, i.e., index on start date is always 100
        self.assertTrue(numpy.isclose(performance_.index_on(datetime.date(2003, 1, 2), 100), 100))
        self.assertTrue(numpy.isclose(performance_.index_on(datetime.date(2003, 2, 1), 100), 96.2944))
        self.assertTrue(numpy.isclose(performance_.index_on(datetime.date(2004, 1, 2), 100), 120.7003))
        self.assertTrue(numpy.isclose(performance_.index_on(datetime.date(2012, 12, 31), 100), 189.6545))

class TestAsset(unittest.TestCase):
    """ Tests the asset class """
    def setUp(self):
        """ Load in data cache """
        self.data_cache = yahoo.load()
        self.asset_factory = asset.AssetFactory(self.data_cache)

    def test_average_yield(self):
        """ REGRESSION Tests the average yield of SPY is each dividend divided by the price on the dividiend issue
            date """

        spy = self.asset_factory.make_asset("SPY")
        self.assertTrue(numpy.isclose(spy.average_yield(), .00462926))

    def test_average_period(self):
        """ REGRESSION tests the average period of SPY is around 3 months """

        spy = self.asset_factory.make_asset("SPY")
        self.assertTrue(numpy.isclose(spy.average_dividend_period(), 89.54167))

    def test_yield_between(self):
        """ Tests the total compound yield of SPY between 2002-1-1 and 2002-12-31 is 1.58%. This has been hand
            calculated"""

        spy = self.asset_factory.make_asset("SPY")
        self.assertTrue(numpy.isclose(spy.yield_between(datetime.date(2002, 1, 1), datetime.date(2002, 12, 31)),
                                      0.0158111178))

    def test_yield_accrued_middle(self):
        """ Tests the yield accrued on 2006-05-01 for the SPY is .215% . This has been hand calculated """

        spy = self.asset_factory.make_asset("SPY")
        self.assertTrue(numpy.isclose(spy.yield_accrued(datetime.date(2006, 5, 1)), 0.002104682))

    def test_yield_accrued_end(self):
        """ At the end, we estimate yield by number of days since last dividend times the average yield.
            This was hand calculated """

        spy = self.asset_factory.make_asset("SPY")
        #last dividend issued on 12-21-12 in data set, making this 41 / average period days in.
        self.assertTrue(numpy.isclose(spy.yield_accrued(datetime.date(2013, 1, 31)), 0.0021196792))

    def test_yield_accrued_early(self):
        """ If we're within one average period of the first dividend, we take the proportion of that that we've
            earned. Hand calculated """

        spy = self.asset_factory.make_asset("SPY")

        #2001, 2, 1 occurs 43, so average_period - 43 / average period is dividend i've earned
        self.assertTrue(numpy.isclose(spy.yield_accrued(datetime.date(2001, 2, 1)),
                        0.0024061812926227))

if __name__ == '__main__':
    unittest.main()
