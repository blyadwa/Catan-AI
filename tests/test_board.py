import os
from board import catanBoard
from hexTile import Resource


def test_board_initialization():
    board = catanBoard()
    assert len(board.hexTileDict) == 19

    deserts = [t for t in board.hexTileDict.values() if t.resource.type == 'DESERT']
    assert len(deserts) == 1
    assert deserts[0].robber is True

    numbers = [t.resource.num for t in board.hexTileDict.values()
               if t.resource.type != 'DESERT']
    expected = [5, 2, 6, 3, 8, 10, 9, 12, 11, 4, 8, 10, 9, 4, 5, 6, 3, 11]
    assert sorted(numbers) == sorted(expected)

    for tile in board.hexTileDict.values():
        assert tile.neighborList is not None
