""" Tests helper algorithms """

from furnace.filter import algorithm

def test_find():
    """ Tests that we find something in a list """
    lst = [1, 5, 10, 15, 20, 22]
    assert algorithm.find(lst, lambda x: x == 15) == 15
