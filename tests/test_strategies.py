import pytest

pytestmark = pytest.mark.core
from symposia.strategies.majority import WeightedMajorityVote
from symposia.strategies.mean import WeightedMeanScore
from symposia.strategies.median import MedianScore


def test_weighted_majority_vote():
    votes = [
        {'value': 'A', 'weight': 2.0},
        {'value': 'B', 'weight': 1.0},
        {'value': 'A', 'weight': 1.0},
    ]
    strategy = WeightedMajorityVote()
    assert strategy.tally(votes) == 'A'


def test_weighted_mean_score():
    votes = [
        {'value': 3, 'weight': 2.0},
        {'value': 5, 'weight': 1.0},
        {'value': 7, 'weight': 1.0},
    ]
    strategy = WeightedMeanScore()
    expected = (3*2 + 5*1 + 7*1) / (2+1+1)
    assert strategy.tally(votes) == expected


def test_median_score_odd():
    votes = [
        {'value': 1}, {'value': 3}, {'value': 2}
    ]
    strategy = MedianScore()
    assert strategy.tally(votes) == 2


def test_median_score_even():
    votes = [
        {'value': 1}, {'value': 4}, {'value': 2}, {'value': 3}
    ]
    strategy = MedianScore()
    assert strategy.tally(votes) == (2+3)/2 