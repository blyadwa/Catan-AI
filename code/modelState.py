#Settlers of Catan
#Model state class for AI training

"""Model state definitions for AI training."""

# Avoid importing heavy modules at import time so this module can be
# imported without side effects.

from typing import Any, Dict, List, Tuple

# ``modelState`` provides a lightweight representation of the current board
# for reinforcement learning.  The module intentionally avoids importing
# heavy packages (``numpy``, ``pygame``) at import time so that unit tests can
# import it without requiring those dependencies.  Any interaction with the
# full game objects is delayed until runtime.

class modelState:
    """Compact representation of the game state for reinforcement learning.

    Parameters
    ----------
    catan_game : Any
        Active game instance containing a ``board`` attribute and a
        ``playerQueue`` with all players.
    player : Any
        The player for whom the state is encoded.  Positive values in the
        vertex and edge arrays correspond to this player while negative values
        represent all opponents.
    """

    def __init__(self, catan_game: Any, player: Any):
        self.game = catan_game
        self.player = player

        self.vertexState: List[int] = []
        self.edgeState: List[int] = []
        self.victoryPoints: List[int] = []
        self.hexTiles: List[Tuple[str, int]] = []
        self.numPlayerCards: List[int] = []
        self.robber: int = -1

        self.edge_index: Dict[Tuple[int, int], int] = {}

        self.update_from_game()

    # ------------------------------------------------------------------
    # State building utilities
    # ------------------------------------------------------------------
    def update_from_game(self) -> None:
        """Recompute the state vectors from ``self.game``."""

        board = self.game.board

        # ------------------------- Vertices -------------------------
        num_vertices = len(board.vertex_index_to_pixel_dict)
        self.vertexState = [0] * num_vertices

        player_queue = list(self.game.playerQueue.queue)

        for idx, pixel in board.vertex_index_to_pixel_dict.items():
            vertex = board.boardGraph[pixel]
            owner = vertex.state["Player"]
            val = 0
            if owner is not None:
                val = 1 if owner is self.player else -1
                if vertex.state["City"]:
                    val *= 2
            self.vertexState[idx] = val

        # --------------------------- Edges ---------------------------
        self.edge_index = {}
        edges: List[Tuple[int, int]] = []
        for idx1, pix1 in board.vertex_index_to_pixel_dict.items():
            v1 = board.boardGraph[pix1]
            for pix2 in v1.edgeList:
                idx2 = next(
                    i for i, p in board.vertex_index_to_pixel_dict.items() if p == pix2
                )
                key = tuple(sorted((idx1, idx2)))
                if key not in self.edge_index:
                    self.edge_index[key] = len(edges)
                    edges.append(key)

        self.edgeState = [0] * len(edges)
        for (i1, i2), e_idx in self.edge_index.items():
            pix1 = board.vertex_index_to_pixel_dict[i1]
            v1 = board.boardGraph[pix1]
            pix2 = board.vertex_index_to_pixel_dict[i2]
            for n_idx, neighbor in enumerate(v1.edgeList):
                if neighbor == pix2 and v1.edgeState[n_idx][1]:
                    owner = v1.edgeState[n_idx][0]
                    self.edgeState[e_idx] = 1 if owner is self.player else -1
                    break

        # ----------------------- Victory Points ----------------------
        self.victoryPoints = [p.visibleVictoryPoints for p in player_queue]

        # ----------------------- Player Card Count -------------------
        self.numPlayerCards = [
            sum(p.resources.values())
            + sum(p.devCards.values())
            + len(p.newDevCards)
            for p in player_queue
        ]

        # ------------------------- Hex Tiles -------------------------
        self.hexTiles = []
        self.robber = -1
        for i in range(len(board.hexTileDict)):
            tile = board.hexTileDict[i]
            self.hexTiles.append((tile.resource.type, tile.resource.num))
            if tile.robber:
                self.robber = i

    # ------------------------------------------------------------------
    # Action enumeration utilities
    # ------------------------------------------------------------------
    def get_valid_actions(self) -> List[Tuple[str, Any]]:
        """Enumerate high level valid actions for ``self.player``."""

        board = self.game.board
        actions: List[Tuple[str, Any]] = []

        # --------------------------------------------------
        # Building: settlements, cities and roads
        # --------------------------------------------------
        if (
            self.player.resources["BRICK"] > 0
            and self.player.resources["WOOD"] > 0
            and self.player.resources["SHEEP"] > 0
            and self.player.resources["WHEAT"] > 0
            and self.player.settlementsLeft > 0
        ):
            for v in board.get_potential_settlements(self.player).keys():
                actions.append(("BUILD_SETTLEMENT", v))

        if (
            self.player.resources["WHEAT"] >= 2
            and self.player.resources["ORE"] >= 3
            and self.player.citiesLeft > 0
        ):
            for v in board.get_potential_cities(self.player).keys():
                actions.append(("BUILD_CITY", v))

        if (
            self.player.resources["BRICK"] > 0
            and self.player.resources["WOOD"] > 0
            and self.player.roadsLeft > 0
        ):
            for edge in board.get_potential_roads(self.player).keys():
                actions.append(("BUILD_ROAD", edge))

        # --------------------------------------------------
        # Development cards
        # --------------------------------------------------
        if (
            self.player.resources["WHEAT"] >= 1
            and self.player.resources["ORE"] >= 1
            and self.player.resources["SHEEP"] >= 1
            and sum(board.devCardStack.values()) > 0
        ):
            actions.append(("DRAW_DEV_CARD", None))

        if not self.player.devCardPlayedThisTurn:
            for card, cnt in self.player.devCards.items():
                if card != "VP" and cnt > 0:
                    actions.append(("PLAY_DEV_CARD", card))

        # --------------------------------------------------
        # Simple bank trades (port logic included)
        # --------------------------------------------------
        actions.extend(self._bank_trade_actions())

        return actions

    def _bank_trade_actions(self) -> List[Tuple[str, Any]]:
        board = self.game.board
        actions: List[Tuple[str, Any]] = []
        ports = self.player.portList
        resources = list(self.player.resources.keys())

        for r1 in resources:
            # Determine the best ratio for r1
            ratio = 4
            if f"2:1 {r1}" in ports:
                ratio = 2
            elif "3:1 PORT" in ports:
                ratio = 3

            if self.player.resources[r1] < ratio:
                continue

            for r2 in resources:
                if r1 == r2 or board.resourceBank[r2] <= 0:
                    continue
                actions.append(("TRADE_BANK", r1, r2, ratio))

        return actions

