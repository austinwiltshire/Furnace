import unittest
import datetime
import data
import performance
import strategy
import numpy

class TestBuyAndHold(unittest.TestCase):
    def test_buy_and_hold(self):
        f = performance.Furnace()
        data_cache = {}
        data_cache["SPY"] = data.load()
        p = f.fire(strategy.BuyAndHoldStocks(data.AssetFactory(data_cache),datetime.date(2001,1,2)))
        self.assertTrue(numpy.isclose(p.CAGR(), 1.00839746759, 1e-11, 1e-11))

if __name__ == '__main__':
    unittest.main()
