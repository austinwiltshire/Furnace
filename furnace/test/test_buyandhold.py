""" Tests strategies and tests known metrics. REGRESSION style tests simply test that known outputs from the models
    do not vary with changes - there is no guarantee that their original values are correct. In many cases, a
    combination of audit (print outputs and calculations, hand check a sample), code review or back of the envelope
    calculations have been used to sanity check the outputs of regression style tests. """

import unittest
import datetime
from furnace.data import asset, yahoo, fcalendar
from furnace import performance, strategy
import numpy

# pylint: disable=R0904
#NOTE: too many public methods
class NumpyTest(unittest.TestCase):
    """ A test case that uses some numpy extensions """
    def assert_close(self, float1, float2, rtol=1e-05, atol=1e-08):
        """ Checks whether two floats are close to eachother """
        self.assertTrue(numpy.isclose(float1, float2, rtol, atol))
# pylint: enable=R0904

# pylint: disable=R0904
#NOTE: too many public methods
class FurnaceTest(NumpyTest):
    """ Test type that tests the furnace module """

    def setUp(self):
        """ Initialize fixture """
        self.data_cache = yahoo.load_pandas()
        self.calendar = fcalendar.make_fcalendar(datetime.datetime(2000, 1, 1))
# pylint: enable=R0904

# pylint: disable=R0904
#NOTE: too many public methods
class TestBuyAndHold(FurnaceTest):
    """ Integration test of trading strategies """

    def setUp(self):
        """ Initialize fixture """
        super(TestBuyAndHold, self).setUp()
        self.begin = datetime.datetime(2001, 1, 2)
        self.end = datetime.datetime(2012, 12, 31)
        self.asset_factory = asset.AssetUniverse(["SPY"], self.data_cache, self.calendar)
        self.strategy = strategy.buy_and_hold_stocks(self.asset_factory, self.begin, self.end)

    def test_buy_and_hold(self):
        """ Tests the simplest buy and hold strategy """

        performance_ = performance.fire_furnace(self.strategy, self.begin, self.end)
        self.assert_close(performance_.cagr(), 1.027589)

    def test_index(self):
        """ Regression Tests indexing a strategy with a base index """

        performance_ = performance.fire_furnace(self.strategy, self.begin, self.end)

        self.assert_close(performance_.growth_by(datetime.datetime(2001, 1, 2)), 1.00)
        self.assert_close(performance_.growth_by(datetime.datetime(2001, 2, 1)), 1.070802)
        self.assert_close(performance_.growth_by(datetime.datetime(2002, 1, 2)), 0.908446)
        self.assert_close(performance_.growth_by(datetime.datetime(2012, 12, 31)), 1.386320)
# pylint: enable=R0904

# pylint: disable=R0904
#NOTE: too many public methods
class TestBondsAndStocks(FurnaceTest):
    """ Test various metrics on a buy and hold portfolio that is 90% stocks and 10% bonds """

    def setUp(self):
        """ Initialize fixture """
        super(TestBondsAndStocks, self).setUp()
        self.begin = datetime.datetime(2003, 1, 2)
        self.end = datetime.datetime(2012, 12, 31)
        self.asset_factory = asset.AssetUniverse(["SPY", "LQD"], self.data_cache, self.calendar)
        self.strategy = strategy.buy_and_hold_stocks_and_bonds(self.asset_factory, self.begin, self.end)


    def test_buy_and_hold(self):
        """ REGRESSION tests mixed portfolio """
        performance_ = performance.fire_furnace(self.strategy, self.begin, self.end)

        self.assert_close(performance_.cagr(), 1.066018)

    def test_index(self):
        """ REGRESSION tests mixed portfolio """
        performance_ = performance.fire_furnace(self.strategy, self.begin, self.end)

        #NOTE: this check below should always be true, i.e., index on start date is always 100
        self.assert_close(performance_.growth_by(datetime.datetime(2003, 1, 2)), 1.0)
        self.assert_close(performance_.growth_by(datetime.datetime(2003, 2, 3)), 0.962289)
        self.assert_close(performance_.growth_by(datetime.datetime(2004, 1, 2)), 1.206420)
        self.assert_close(performance_.growth_by(datetime.datetime(2012, 12, 31)), 1.895492)

    def test_new_index_spy(self):
        """ Test that new pandas style index matches up with returns for spy calculated via adjusted close """
        from furnace import portfolio

        index = portfolio.make_index([portfolio.Weighting(self.asset_factory.make_asset("SPY"), 1.0)],
                                     datetime.datetime(2003, 1, 2))

        #calculate yahoo's dividend adjusted return
        spy = self.asset_factory.make_asset("SPY")
        adj_close = spy.table()[spy.table().index >= datetime.datetime(2003, 1, 2)]['Adj Close']
        first = adj_close.ix[0]
        last = adj_close.ix[len(adj_close)-1]
        adj_return = (last - first) / first

        self.assert_close(index.total_return_by(datetime.datetime(2012, 12, 31)), adj_return, rtol=1e-03)

    def test_new_index_lqd(self):
        """ Test that new pandas style index matches up with returns for lqd calculated via adjusted close """
        from furnace import portfolio

        index = portfolio.make_index([portfolio.Weighting(self.asset_factory.make_asset("LQD"), 1.0)],
                                     datetime.datetime(2003, 1, 2))

        #calculate yahoo's dividend adjusted return
        lqd = self.asset_factory.make_asset("LQD")
        adj_close = lqd.table()[lqd.table().index >= datetime.datetime(2003, 1, 2)]['Adj Close']
        first = adj_close.ix[0]
        last = adj_close.ix[len(adj_close)-1]
        adj_return = (last - first) / first

        self.assert_close(index.total_return_by(datetime.datetime(2012, 12, 31)), adj_return, rtol=1e-03)

    def test_new_index_spy_lqd(self):
        """ REGRESSION test of a half and half indexed portfolio """
        #NOTE: Adjusted close floats with time, meaning with different data adjusted close changes even on the same
        #dates. This does not always seem geometrically stable as long term returns can shift even though they've
        #'already' happened. This is one benefit of using one stable understood system than relying on yahoo's black
        #magic adjusted close.
        from furnace import portfolio

        index = portfolio.make_index([portfolio.Weighting(self.asset_factory.make_asset("LQD"), 0.5),
                                      portfolio.Weighting(self.asset_factory.make_asset("SPY"), 0.5)],
                                     datetime.datetime(2003, 1, 2))

        adj_return = .883 #pre calculated
        self.assert_close(index.total_return_by(datetime.datetime(2012, 12, 31)), adj_return, rtol=1e-03)

    def test_volatility(self):
        """ TDD smoke test """
        from furnace import portfolio

        performance_ = performance.fire_furnace(self.strategy, self.begin, self.end)
        vol = performance_.volatility()

        self.assert_close(vol, 0.163339)
# pylint: enable=R0904

# pylint: disable=R0904
#NOTE: too many public methods
class TestAsset(NumpyTest):
    """ Tests the asset class """
    def setUp(self):
        """ Load in data cache """
        self.data_cache = yahoo.load_pandas()
        self.calendar = fcalendar.make_fcalendar(datetime.datetime(2000, 1, 1))
        self.asset_factory = asset.AssetUniverse(["SPY"], self.data_cache, self.calendar)
        self.spy = self.asset_factory.make_asset("SPY")

    def test_average_yield(self):
        """ REGRESSION Tests the average yield of SPY is each dividend divided by the price on the dividiend issue
            date """

        self.assert_close(self.spy.average_yield(), .00462926)

    def test_average_period(self):
        """ REGRESSION tests the average period of SPY is around 3 months """

        self.assert_close(self.spy.average_dividend_period(), 89.54167)

    def test_yield_between(self):
        """ Tests the total compound yield of SPY between 2002-1-1 and 2002-12-31 is 1.58%. This has been hand
            calculated"""

        begin = datetime.datetime(2002, 1, 1)
        end = datetime.datetime(2002, 12, 31)
        self.assert_close(self.spy.yield_between(begin, end), 0.0158111178)

    def test_yield_accrued_middle(self):
        """ Tests the yield accrued on 2006-05-01 for the SPY is .215% . This has been hand calculated """

        self.assert_close(self.spy.yield_accrued(datetime.datetime(2006, 5, 1)), 0.002104682)

    def test_yield_accrued_end(self):
        """ At the end, we estimate yield by number of days since last dividend times the average yield.
            This was hand calculated """

        #last dividend issued on 12-21-12 in data set, making this 41 / average period days in.
        self.assert_close(self.spy.yield_accrued(datetime.datetime(2013, 1, 31)), 0.0021196792)

    def test_yield_accrued_early(self):
        """ If we're within one average period of the first dividend, we take the proportion of that that we've
            earned. Hand calculated """

        #2001, 2, 1 occurs 43, so average_period - 43 / average period is dividend i've earned
        self.assert_close(self.spy.yield_accrued(datetime.datetime(2001, 2, 1)),
                        0.0024061812926227)
# pylint: enable=R0904

if __name__ == '__main__':
    unittest.main()
