import os
import sys
import types
import pytest

# Provide lightweight stubs for external dependencies used by the code module
numpy_stub = types.ModuleType('numpy')
numpy_stub.random = types.SimpleNamespace(
    randint=lambda *a, **k: 1,
    permutation=lambda x: list(x),
)
sys.modules.setdefault('numpy', numpy_stub)

pygame_stub = types.ModuleType('pygame')
pygame_stub.init = lambda: None
sys.modules.setdefault('pygame', pygame_stub)

board_stub = types.ModuleType('board')
board_stub.deposit_resource = lambda *a, **k: None
board_stub.withdraw_resource = lambda *a, **k: True
board_stub.catanBoard = object
sys.modules.setdefault('board', board_stub)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from heuristicAIPlayer import heuristicAIPlayer


def make_player(name):
    p = heuristicAIPlayer(name, 'red')
    p.updateAI()
    return p


def test_propose_trade_with_players():
    p1 = make_player('p1')
    p2 = make_player('p2')
    # p1 has plenty of brick but no sheep
    p1.resources.update({'BRICK': 2, 'WOOD': 1, 'WHEAT': 1, 'SHEEP': 0, 'ORE': 0})
    # p2 can supply sheep
    p2.resources.update({'BRICK': 0, 'WOOD': 0, 'WHEAT': 1, 'SHEEP': 2, 'ORE': 0})

    trade = p1.propose_trade_with_players([p1, p2])
    assert trade is not None
    player, offer, request = trade
    assert player is p2
    assert offer == {'BRICK': 1}
    assert request == {'SHEEP': 1}


def test_accept_trade():
    p = make_player('p')
    p.resources.update({'BRICK': 3, 'WOOD': 0, 'WHEAT': 1, 'SHEEP': 0, 'ORE': 0})
    # Offer wood for brick
    assert p.accept_trade({'WOOD': 1}, {'BRICK': 1})
    # Even a larger offer is accepted since wood is lacking
    assert p.accept_trade({'WOOD': 1}, {'BRICK': 2})


def test_get_action_priority():
    p = make_player('p')
    p.resources.update({'ORE': 3, 'WHEAT': 2, 'BRICK': 0, 'WOOD': 0, 'SHEEP': 0})
    assert p.get_action() == ('BUILD_CITY',)

    p.resources.update({'ORE': 0, 'WHEAT': 1, 'BRICK': 1, 'WOOD': 1, 'SHEEP': 1})
    assert p.get_action() == ('BUILD_SETTLEMENT',)

    p.resources.update({'BRICK': 1, 'WOOD': 1, 'SHEEP': 0, 'WHEAT': 0, 'ORE': 0})
    assert p.get_action() == ('BUILD_ROAD',)

    # Trade when lacking sheep but abundant brick
    p2 = make_player('p2')
    p.resources.update({'BRICK': 2, 'WOOD': 0, 'SHEEP': 0, 'WHEAT': 0, 'ORE': 0})
    p2.resources.update({'SHEEP': 1})
    action = p.get_action([p2])
    assert action[0] == 'TRADE_PLAYER'

    # Nothing to do
    p.resources.update({'BRICK': 0, 'WOOD': 0, 'SHEEP': 0, 'WHEAT': 0, 'ORE': 0})
    assert p.get_action([p2]) == ('PASS',)


def test_execute_action_build_settlement_and_trade():
    p1 = make_player('p1')
    p2 = make_player('p2')
    p1.resources.update({'BRICK': 1, 'WOOD': 1, 'SHEEP': 1, 'WHEAT': 1, 'ORE': 0})
    # Build settlement without board
    assert p1.execute_action(('BUILD_SETTLEMENT',))
    assert p1.resources['BRICK'] == 0
    assert p1.victoryPoints == 1

    # Trade with p2
    p1.resources.update({'BRICK': 1})
    p2.resources.update({'SHEEP': 1})
    action = ('TRADE_PLAYER', p2, {'BRICK': 1}, {'SHEEP': 1})
    assert p1.execute_action(action)
    assert p1.resources['BRICK'] == 0
    assert p1.resources['SHEEP'] == 1
    assert p2.resources['BRICK'] == 1
