from board import catanBoard
from player import player


def test_player_build_methods():
    board = catanBoard()
    p = player('P1', 'red')

    v1 = list(board.boardGraph.keys())[0]
    v2 = board.boardGraph[v1].edgeList[0]

    p.build_road(v1, v2, board, free=True)
    assert (v1, v2) in p.buildGraph['ROADS']
    idx = board.boardGraph[v1].edgeList.index(v2)
    assert board.boardGraph[v1].edgeState[idx][1] is True

    p.build_settlement(v1, board, free=True)
    assert v1 in p.buildGraph['SETTLEMENTS']
    assert board.boardGraph[v1].state['Settlement'] is True

    p.resources['ORE'] = 3
    p.resources['WHEAT'] = 2
    p.build_city(v1, board)
    assert v1 in p.buildGraph['CITIES']
    assert board.boardGraph[v1].state['City'] is True
