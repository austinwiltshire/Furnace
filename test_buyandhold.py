""" Tests strategies and tests known metrics """

import unittest
import datetime
import data
import performance
import strategy
import numpy

class TestBuyAndHold(unittest.TestCase):
    """ Integration test of trading strategies """

    def test_buy_and_hold(self):
        """ Tests the simplest buy and hold strategy """
        furnace = performance.Furnace()
        data_cache = {}
        data_cache["SPY"] = data.load()
        performance_ = furnace.fire(strategy.BuyAndHoldStocks(data.AssetFactory(data_cache),datetime.date(2001,1,2)))
        self.assertTrue(numpy.isclose(performance_.CAGR(), 1.00839746759, 1e-11, 1e-11))

if __name__ == '__main__':
    unittest.main()
