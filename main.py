""" A utility file for rapid prototyping """

# Initial prototype
# Needs to make a mock strategy 
# - A mock forecast (forecaster module called weatherman?)
# - A mock portfolio optimizer
# Initial testing framework that loads in asset class information
# Runs initial test

# The portfolio optimizer knows what the metrics it needs to optimize are, and those metrics
# Ultimately are the output variables of what the forecast needs to generate. So in terms of 
# strategy, the portfolio optimizer shoudl be feeding in to the weatherman what he needs to be
# predicting.

#Given a time point, returns a forecast of key metrics for an asset class
#over a corresponding period
#First metrics will be expected return, expected volatility and expected correlation

#Steps:
# - Implement a buy and hold on the spy strategy
# - Implement an 80%/20% strategy of spy and lqd

# Ultimately the metrics forecasted as inputs for the optimizer are part of the financial strategy and may have different models for each one

def main():
    """ Whatever is being prototyped can be put in here """
    pass

if "__main__" == __name__:
    main()
