from board import catanBoard
from player import player
from hexTile import Resource


def test_draw_and_update_dev_cards():
    board = catanBoard()
    board.devCardStack = {'KNIGHT': 1}
    p = player('P1', 'blue')
    p.resources['ORE'] = 1
    p.resources['WHEAT'] = 1
    p.resources['SHEEP'] = 1

    p.draw_devCard(board)
    assert board.devCardStack['KNIGHT'] == 0
    assert p.newDevCards == ['KNIGHT']
    p.updateDevCards()
    assert p.devCards['KNIGHT'] == 1


def test_draw_vp_card():
    board = catanBoard()
    board.devCardStack = {'VP': 1}
    p = player('P2', 'green')
    p.resources['ORE'] = 1
    p.resources['WHEAT'] = 1
    p.resources['SHEEP'] = 1

    p.draw_devCard(board)
    assert board.devCardStack['VP'] == 0
    assert p.victoryPoints == 1
    assert p.devCards['VP'] == 1
