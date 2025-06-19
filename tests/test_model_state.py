import queue
import types

from board import catanBoard
from player import player
from modelState import modelState


def make_game(num_players=2):
    board = catanBoard()
    players = [player(f"P{i+1}", "color") for i in range(num_players)]
    q = queue.Queue()
    for p in players:
        q.put(p)
    game = types.SimpleNamespace(board=board, playerQueue=q)
    return game, players


def test_update_from_game_basic():
    game, players = make_game(2)
    p1, p2 = players
    v0 = game.board.vertex_index_to_pixel_dict[0]
    v1 = game.board.boardGraph[v0].edgeList[0]
    idx1 = next(i for i, px in game.board.vertex_index_to_pixel_dict.items() if px == v1)

    p1.build_road(v0, v1, game.board, free=True)
    p1.build_settlement(v0, game.board, free=True)
    game.board.updateBoardGraph_robber(3)

    state = modelState(game, p1)

    assert state.vertexState[0] == 1
    edge_key = tuple(sorted((0, idx1)))
    assert state.edgeState[state.edge_index[edge_key]] == 1
    assert state.victoryPoints == [1, 0]
    assert state.robber == 3
    assert len(state.hexTiles) == len(game.board.hexTileDict)
    assert state.numPlayerCards == [0, 0]


def test_get_valid_actions():
    game, players = make_game(1)
    p = players[0]
    board = game.board

    board.get_potential_settlements = lambda player: {0: True}
    board.get_potential_cities = lambda player: {0: True}
    board.get_potential_roads = lambda player: {(0, 1): True}

    board.devCardStack = {"KNIGHT": 1}
    board.resourceBank = {r: 1 for r in ["ORE", "BRICK", "WHEAT", "WOOD", "SHEEP"]}

    p.resources.update({"BRICK": 4, "WOOD": 1, "SHEEP": 1, "WHEAT": 2, "ORE": 3})
    p.devCards["KNIGHT"] = 1
    p.portList.append("3:1 PORT")

    state = modelState(game, p)
    actions = state.get_valid_actions()

    assert ("BUILD_SETTLEMENT", 0) in actions
    assert ("BUILD_CITY", 0) in actions
    assert ("BUILD_ROAD", (0, 1)) in actions
    assert ("DRAW_DEV_CARD", None) in actions
    assert ("PLAY_DEV_CARD", "KNIGHT") in actions
    assert ("TRADE_BANK", "BRICK", "ORE", 3) in actions
