""" Common helper algorithms and utilities """

def find(list_, predicate):
    """ Common find idiom - returns the element in a list that satisfies a predicate
    Asserts that there is only one answer """

    answer = [item for item in list_ if predicate(item)]
    assert 1 == len(answer)
    return answer[0]
