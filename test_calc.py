import pytest
from Calc import *

def test_add():
    assert add(2,3) == 5
    assert add(1,1) == 2

def test_subs():
    assert subs(5,3) == 2

def test_mult():
    assert mult(2,3) == 6

def test_divide():
    assert divide(6,3) == 2

def test_divide_by_zero():
    with pytest.raises(ValueError):
        divide(6,0)

