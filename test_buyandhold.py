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
        self.data_cache = {"SPY": data.load()}
        self.asset_factory = data.AssetFactory(self.data_cache)

    def test_buy_and_hold(self):
        """ Tests the simplest buy and hold strategy """
        #TODO: move "data cache" into the data.py
        #NOTE: data_cache will be eager loaded (current design, anyway)

        performance_ = self.furnace.fire(strategy.BuyAndHoldStocks(self.asset_factory, datetime.date(2001, 1, 2)))
        self.assertTrue(numpy.isclose(performance_.CAGR(), 1.00839746759, 1e-11, 1e-11))

    def test_index_price(self):
        """ Tests indexing a strategy using a base price"""

        spy = self.asset_factory.make_asset("SPY")
        strat = strategy.BuyAndHoldStocks(self.asset_factory, datetime.date(2001, 1, 2))
        performance_ = self.furnace.fire(strat)
        base = spy.price(datetime.date(2001, 1, 2))

        self.assertTrue(numpy.isclose(performance_.index_on(datetime.date(2001, 1, 2), base), 128.81))
        self.assertTrue(numpy.isclose(performance_.index_on(datetime.date(2001, 2, 1), base), 137.93))
        self.assertTrue(numpy.isclose(performance_.index_on(datetime.date(2002, 1, 2), base), 115.53))
        self.assertTrue(numpy.isclose(performance_.index_on(datetime.date(2012, 12, 31), base), 142.41))

    def test_index_index(self):
        """ Tests indexing a strategy with a base index """
        strat = strategy.BuyAndHoldStocks(self.asset_factory, datetime.date(2001, 1, 2))
        performance_ = self.furnace.fire(strat)

        self.assertTrue(numpy.isclose(performance_.index_on(datetime.date(2001, 1, 2), 100), 100))
        self.assertTrue(numpy.isclose(performance_.index_on(datetime.date(2001, 2, 1), 100), 107.0801))
        self.assertTrue(numpy.isclose(performance_.index_on(datetime.date(2002, 1, 2), 100), 89.69))
        self.assertTrue(numpy.isclose(performance_.index_on(datetime.date(2012, 12, 31), 100), 110.5581))


if __name__ == '__main__':
    unittest.main()
