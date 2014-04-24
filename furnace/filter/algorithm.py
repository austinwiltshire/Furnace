"""
Common helper algorithms and utilities
"""

def find(list_, predicate):
    """ Common find idiom - returns the element in a list that satisfies a predicate, asserts that there is only one
    answer """
    answer = [p for p in list_ if predicate(p)]
    assert 1 == len(answer)
    return answer[0]
