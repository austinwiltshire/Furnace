""" A utility file for rapid prototyping """
import performance
import data
import numpy
import strategy
import datetime
import matplotlib.pyplot as plt

def main():
    """ Whatever is being prototyped can be put in here """
    furnace = performance.Furnace()

    #NOTE: data_cache will be eager loaded (current design, anyway)
    data_cache = {}
    data_cache["SPY"] = data.load()

    asset_factory = data.AssetFactory(data_cache)
    strat = strategy.BuyAndHoldStocks(asset_factory,
                                      datetime.date(2001, 1, 2))
    performance_ = furnace.fire(strat)

    data_ = []
    for date_ in range(performance_.days()+1):
        data_.append((performance_.begin() + datetime.timedelta(date_),
                     performance_.index_on(performance_.begin() + datetime.timedelta(date_), 100.0)))

    time_axis = numpy.array([x[0] for x in data_])
    index_value = numpy.array([x[1] for x in data_])
    plt.plot(time_axis, index_value)
    plt.show()
    #TODO: move these plots over to non pyplot so that they can be eaisly analyzed and combined without looking
    #at them


if "__main__" == __name__:
    main()
