""" Performance tracking """

import numpy
import pandas
import datetime
import itertools
import re
import furnace.data.fcalendar

def reindex(table1, table2):
    """ Reindexes table2 to have basis the same as end of table1. modifies it's second argument """
    assert table1.ix[-1].name == table2.ix[0].name, "last index of table1 ought to be first of table2"

    multiplier = table1.ix[-1]['index'] / table2.ix[0]['index']

    #recalculate basis
    new_basis = table2.filter(regex=".*_Basis") * multiplier

    #reset table2's basis
    for column in new_basis.columns:
        table2[column] = new_basis[column]

    #recalculate asset indecies
    #TODO: consider renaming asset universe to basket
    index_regex = re.compile("(?P<symbol>.*)_Index")
    symbols = [
        index_regex.match(column).group('symbol')
        for column
        in table2.filter(regex=".*_Index").columns
    ]

    symbols1 = [
        index_regex.match(column).group('symbol')
        for column
        in table1.filter(regex=".*_Index").columns
    ]

    assert set(symbols) == set(symbols1), "Both tables should have same symbols"

    for symbol in symbols:
        table2[symbol + "_Index"] = table2[symbol + "_Basis"] * table2[symbol + "_AdjustedPrice"]

    #recalculate portfolio index
    table2["index"] = table2.filter(regex=".*_Index").sum(axis=1)

    #returns second arg for convenience
    return table2

def make_overall_performance(portfolio_periods, asset_factory):
    """ Factory function to create overall performances """

    #group periods into pairs to reindex the latter on the former
    period_pairs = zip(portfolio_periods[:-1], portfolio_periods[1:])
    assert all(period_pair[0].end() == period_pair[1].begin() for period_pair in period_pairs)

    #reindex one by one - must go in ascending order.
    #periods are reindexed *in place* so that by the time one is reindexed, it's ready to serve
    #as the reference for the next
    for period_pair in period_pairs:
        reindex(period_pair[0]._table, period_pair[1]._table)

    overall_period = pandas.concat(period._table for period in portfolio_periods)
    overall_period['date'] = overall_period.index
    overall_period.drop_duplicates(cols=['date'], take_last=True, inplace=True)

    assert overall_period.ix[0].name == portfolio_periods[0].begin()
    assert overall_period.ix[-1].name == portfolio_periods[-1].end()

    #TODO: consider 'fillna' rather than 'dropna'. this would fill the first day with 0.0 on daily and 
    #cumulative growth which is correct
    overall_period["Daily Returns"] = overall_period["index"].pct_change().dropna()
    overall_period = overall_period.dropna()
    overall_period["Cumulative Returns"] = ((overall_period["Daily Returns"] + 1.0).cumprod() - 1.0)

    return OverallPerformance(portfolio_periods, asset_factory, overall_period)

class OverallPerformance(object):
    """ OverallPerformance is how a strategy does over time. """

    def __init__(self, portfolio_periods, asset_factory, table):
        """ Currently expects a dict of dates to portfolios. Period performances are inclusive of end
        dates and exclusive of begin dates. That means altogether, they're inclusive of the entire trading
        period and it's end and exclusive of it's end. We have a single special case to handle that in
        overall performance. """
        self._portfolio_periods = portfolio_periods
        self._asset_factory = asset_factory
        self._table = table

        self.__invariant()

    def __invariant(self):
        """ Object invariants. This adds about a second to testing and can be turned off """
        assert sorted(self._portfolio_periods, key=PeriodPerformance.begin) == self._portfolio_periods
        assert not any(
            period1.overlaps_with(period2)
            for period1, period2 in itertools.product(self._portfolio_periods, self._portfolio_periods)
            if period1 is not period2
        )

    def total_return(self):
        """ Returns the total return from begining to end """
        self.__invariant()
        return self.growth_by(self.end())

#TODO: add assertion that len(self._table.index) == number of trading days between begin and end in financial calendar
#TODO: to do the above i'd need to pass in a fcalendar 
    def duration(self):
        """ Returns the length of this performance period in trading days"""
        self.__invariant()
        return datetime.timedelta(len(self._table.index))

    def cagr(self):
        """ Returns the compound annual growth rate """
        self.__invariant()
        return pow(
            1.0 + self.total_return(),
            1.0 / (self.duration().days / furnace.data.fcalendar.trading_days_in_year())
        ) - 1.0

    def expected_return(self):
        """ Returns the expected daily return """
        self.__invariant()
        return self._table["Daily Returns"].mean()

    def volatility(self):
        """ Returns the simple daily volatility of price movements, as a percent, of this entire performance period """
        self.__invariant()
        #NOTE: http://wiki.fool.com/How_to_Calculate_the_Annualized_Volatility
        return numpy.sqrt(furnace.data.fcalendar.trading_days_in_year()*self._table["Daily Returns"].var())

    def growth_by(self, date):
        """ Returns growth by a date as a percent on beginning date of this performance """
        self.__invariant()
        if date == self.begin():
            return 0.0
        return self._table["Cumulative Returns"][date]

    def plot_index(self, index_base):
        """ Plots a day by day performance, with day one pegged at value of index_base, on a matplotlib chart """
        self.__invariant()

        indecies = (1.0 + self._table["Cumulative Returns"]) * index_base
        return indecies.plot()

    def begin(self):
        """ Returns beginning date of this performance period """
        self.__invariant()
        return self._portfolio_periods[0].begin()

    def end(self):
        """ Returns ending date of this performance period """
        self.__invariant()
        return self._portfolio_periods[-1].end()

    def simple_sharpe(self):
        """ Returns a simplified sharpe ratio - cagr over volatility. """
        self.__invariant()
        return self.cagr() / self.volatility()

    def number_of_trades(self):
        """ Simple turnover metric - an estimate of the number of trades we make """
        self.__invariant()
        trades = self.__trade_table()

        return len(trades) * len(trades.columns)

    #TODO: hand test this on a yearly rebalance of spy and lqd as see in
    #test/test_performance.py:test_number_of_trades_yearly. Can depend on the basis calculations
    #of the first period, but then check that the returns of such basis changes are correct by hand
    #using my own adjusted close
    def __trade_table(self):
        """ Constructs a table of what trades would be made and when to recreate the index performance """
        self.__invariant()

        basis = self._table.filter(regex=".*_Basis")

        #Only NA to be filled is the first day, which we fill with the first day's basis since the
        #'day before', not represented in the series, would have had a 0 basis.
        deltas = basis.diff().fillna(basis)

        #NOTE: this does not remove basis diffs that are astoundingly close to zero
        deltas = deltas[(deltas != 0.0)].dropna()

        #Add on the last day as a negative, since we will be 'selling' our entire basis that day
        return deltas.append(-basis.ix[-1])

    def growth_curve(self, principle, comissions):
        """ Simulates the actual performance of a certain amount of cash, charging comissions """

        trades = self.__trade_table()
        trades['Comissions'] = comissions
        table = self._table[['Daily Returns']] + 1.0
        table['Comissions'] = trades['Comissions']
        table['Comissions'].fillna(0.0, inplace=True)
        number_assets = len(self._table.filter(regex=".*_Basis").columns)

        def principle_accumulator(principle):
            """ Wrapper that returns a stateful apply that calculates principle growth """

            nonlocal = {"principle":principle} # python 2.7 'mutable closure'
            def _(row):
                """ Inner helper function to provide a stateful apply that calculates principle growth """

                total_comissions = row["Comissions"] * number_assets
                nonlocal["principle"] = nonlocal["principle"] * row["Daily Returns"] - total_comissions
                return nonlocal["principle"]
            return _

        accumulator = principle_accumulator(principle)

        return table.apply(accumulator, axis=1)

def make_period_performance(begin_date, end_date, index):
    """ Factory for a period performance object """
    assert index.table.index[0] == begin_date
    assert index.table.index[-1] == end_date
    return PeriodPerformance(begin_date, end_date, index.table)

class PeriodPerformance(object):
    """ How a strategy does over it's trading period. A period performance is exclusive of it's begin
    date and inclusive of it's end date. In other words, if we had a period performance that started
    today, the soonest we'd have data available is tomorrow since today is our 'buy' point
    Our performance today, for example, is always 0%. """

    def __init__(self, begin_date, end_date, table):
        self._begin_date = begin_date
        self._end_date = end_date
        self._table = table

    def daily_returns(self):
        """ Returns a daily series of this period's returns """
        return self._table["index"].pct_change().dropna()

    def number_of_days(self):
        """ Returns number of trading days in this period """
        return len(self._table)

    def begin(self):
        """ Returns start date of this period """
        return self._begin_date

    def end(self):
        """ Return end date of this performance period """
        return self._end_date

    def overlaps_with(self, other):
        """ Returns true if this period overlaps with other period """
        return self.end() > other.begin() if self.begin() < other.begin() else other.end() > self.begin()
