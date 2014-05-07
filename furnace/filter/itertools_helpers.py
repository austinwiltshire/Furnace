"""
Itertool extensions and helpers
"""

import itertools

def self_cartesian_map(list_, functor):
    """ Maps the cartesian of a list with itself, excluding identity relations, through some functor """
    return [functor(first, second) for (first, second) in itertools.product(list_, list_) if first is not second]
