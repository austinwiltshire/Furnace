""" Tests strategies and tests known metrics """

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
        self.assertTrue(numpy.isclose(performance_.CAGR(), 1.00839746759, 1e-11, 1e-11))

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

class TestAsset(unittest.TestCase):
    """ Tests the asset class """
    def setUp(self):
        """ Load in data cache """
        self.data_cache = data.load()
        self.asset_factory = data.AssetFactory(self.data_cache)

#    def test_dividend(self):
#        """ Test that we grab the right dividend amount on 10-10-2010 """
#        spy = self.asset_factory.make_asset("SPY")
#        self.assertTrue(numpy.isclose(spy.trailing_dividend(datetime.date(2010, 10, 10)), 2.203))

#    def test_dividend_period(self):
#        """ Test that we grab the right length of time for 10-10-2010 """
#        spy = self.asset_factory.make_asset("SPY")
#        self.assertEqual(spy.dividend_period(datetime.date(2010, 10, 10)).days, 91)

#    def test_yield(self):
#        """ Test the yield calculation on 10-10-2010 """
#        spy = self.asset_factory.make_asset("SPY")
#        self.assertTrue(numpy.isclose(spy.trailing_yield(datetime.date(2010, 10, 10)), 0.018903380813454))

#TODO: add unit test for yield

if __name__ == '__main__':
    unittest.main()
