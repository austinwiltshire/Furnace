""" Tests strategies and tests known metrics. REGRESSION style tests simply test that known outputs from the models
    do not vary with changes - there is no guarantee that their original values are correct. In many cases, a
    combination of audit (print outputs and calculations, hand check a sample), code review or back of the envelope
    calculations have been used to sanity check the outputs of regression style tests. """

import unittest
import datetime
import data
import performance
import strategy
import numpy

class TestBuyAndHold(unittest.TestCase):
    """ Integration test of trading strategies """

    def setUp(self):
        """ Initialize fixture """
        self.furnace = performance.Furnace()
        self.data_cache = data.load() 
        self.asset_factory = data.AssetFactory(self.data_cache)

    def test_buy_and_hold(self):
        """ Tests the simplest buy and hold strategy """
        #TODO: move "data cache" into the data.py
        #NOTE: data_cache will be eager loaded (current design, anyway)

        begin = datetime.date(2001, 1, 2)
        end = datetime.date(2012, 12, 31)
        performance_ = self.furnace.fire(strategy.BuyAndHoldStocks(self.asset_factory, begin), begin, end)
        self.assertTrue(numpy.isclose(performance_.CAGR(), 1.02763283748, 1e-11, 1e-11))

    def test_index_index(self):
        """ Tests indexing a strategy with a base index """

        #TODO: should i grab begin and end from the data cache?
        begin = datetime.date(2001, 1, 2)
        end = datetime.date(2012, 12, 31)
        strat = strategy.BuyAndHoldStocks(self.asset_factory, datetime.date(2001, 1, 2))
        performance_ = self.furnace.fire(strat, begin, end)
       
        self.assertTrue(numpy.isclose(performance_.index_on(datetime.date(2001, 1, 2), 100), 100))
        self.assertTrue(numpy.isclose(performance_.index_on(datetime.date(2001, 2, 1), 100), 107.3378))
        self.assertTrue(numpy.isclose(performance_.index_on(datetime.date(2002, 1, 2), 100), 91.0677))
        self.assertTrue(numpy.isclose(performance_.index_on(datetime.date(2012, 12, 31), 100), 138.7037))

class TestBondsAndStocks(unittest.TestCase):
    """ Test various metrics on a buy and hold portfolio that is 90% stocks and 10% bonds """

    def setUp(self):
        """ Initialize fixture """
        self.furnace = performance.Furnace()
        self.data_cache = data.load() 
        self.asset_factory = data.AssetFactory(self.data_cache)

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
        self.assertTrue(numpy.isclose(performance_.index_on(datetime.date(2003, 2, 1), 100), 96.3109))
        self.assertTrue(numpy.isclose(performance_.index_on(datetime.date(2004, 1, 2), 100), 121.0233))
        self.assertTrue(numpy.isclose(performance_.index_on(datetime.date(2012, 12, 31), 100), 189.6545))

class TestAsset(unittest.TestCase):
    """ Tests the asset class """
    def setUp(self):
        """ Load in data cache """
        self.data_cache = data.load()
        self.asset_factory = data.AssetFactory(self.data_cache)

    def test_average_yield(self):
        """ REGRESSION Tests the average yield of SPY is each dividend divided by the price on the dividiend issue
            date """

        spy = self.asset_factory.make_asset("SPY")
        self.assertTrue(numpy.isclose(spy.average_yield(), .00462926))

if __name__ == '__main__':
    unittest.main()
