#Settlers of Catan
#Heuristic AI class implementation

from board import *
from player import *
import numpy as np

#Class definition for an AI player
class heuristicAIPlayer(player):
    
    #Update AI player flag and resources
    def updateAI(self): 
        self.isAI = True
        self.setupResources = [] #List to keep track of setup resources
        #Players start with no resources and collect them after initial setup
        self.resources = {'ORE':0, 'BRICK':0, 'WHEAT':0, 'WOOD':0, 'SHEEP':0}
        print("Added new AI Player:", self.name)


    #Function to build an initial settlement - just choose random spot for now
    def initial_setup(self, board, game=None):
        #Build random settlement
        possibleVertices = board.get_setup_settlements(self)

        #Simple heuristic for choosing initial spot
        diceRoll_expectation = {2:1, 3:2, 4:3, 5:4, 6:5, 8:5, 9:4, 10:3, 11:2, 12:1, None:0}
        vertexValues = []

        #Get the adjacent hexes for each hex
        for v in possibleVertices.keys():
            vertexNumValue = 0
            resourcesAtVertex = []
            #For each adjacent hex get its value and overall resource diversity for that vertex
            for adjacentHex in board.boardGraph[v].adjacentHexList:
                resourceType = board.hexTileDict[adjacentHex].resource.type
                if(resourceType not in resourcesAtVertex):
                    resourcesAtVertex.append(resourceType)
                numValue = board.hexTileDict[adjacentHex].resource.num
                vertexNumValue += diceRoll_expectation[numValue] #Add to total value of this vertex

            #basic heuristic for resource diversity
            vertexNumValue += len(resourcesAtVertex)*2
            for r in resourcesAtVertex:
                if(r != 'DESERT' and r not in self.setupResources):
                    vertexNumValue += 2.5 #Every new resource gets a bonus
            
            vertexValues.append(vertexNumValue)


        vertexToBuild_index = vertexValues.index(max(vertexValues))
        vertexToBuild = list(possibleVertices.keys())[vertexToBuild_index]

        #Add to setup resources
        for adjacentHex in board.boardGraph[vertexToBuild].adjacentHexList:
            resourceType = board.hexTileDict[adjacentHex].resource.type
            if(resourceType not in self.setupResources and resourceType != 'DESERT'):
                self.setupResources.append(resourceType)

        #Free placement during initial setup
        built = self.build_settlement(vertexToBuild, board, free=True)
        if built and game is not None:
            for p in list(game.playerQueue.queue):
                game.check_longest_road(p)


        #Build random road
        possibleRoads = board.get_setup_roads(self)
        randomEdge = np.random.randint(0, len(possibleRoads.keys()))
        self.build_road(list(possibleRoads.keys())[randomEdge][0],
                        list(possibleRoads.keys())[randomEdge][1],
                        board, free=True)

    
    def move(self, board, game=None):
        print("AI Player {} playing...".format(self.name))
        #Trade resources if there are excessive amounts of a particular resource
        self.trade(board)
        #Build a settlements, city and few roads
        possibleVertices = board.get_potential_settlements(self)
        if(possibleVertices != {} and (self.resources['BRICK'] > 0 and self.resources['WOOD'] > 0 and self.resources['SHEEP'] > 0 and self.resources['WHEAT'] > 0)):
            randomVertex = np.random.randint(0, len(possibleVertices.keys()))
            built = self.build_settlement(list(possibleVertices.keys())[randomVertex], board)
            if built and game is not None:
                for p in list(game.playerQueue.queue):
                    game.check_longest_road(p)

        #Build a City
        possibleVertices = board.get_potential_cities(self)
        if(possibleVertices != {} and (self.resources['WHEAT'] >= 2 and self.resources['ORE'] >= 3)):
            randomVertex = np.random.randint(0, len(possibleVertices.keys()))
            built_city = self.build_city(list(possibleVertices.keys())[randomVertex], board)
            if built_city and game is not None:
                for p in list(game.playerQueue.queue):
                    game.check_longest_road(p)

        #Build a couple roads
        for i in range(2):
            if(self.resources['BRICK'] > 0 and self.resources['WOOD'] > 0):
                possibleRoads = board.get_potential_roads(self)
                randomEdge = np.random.randint(0, len(possibleRoads.keys()))
                self.build_road(list(possibleRoads.keys())[randomEdge][0], list(possibleRoads.keys())[randomEdge][1], board)

        #Draw a Dev Card with 1/3 probability
        devCardNum = np.random.randint(0, 3)
        if(devCardNum == 0):
            self.draw_devCard(board)
        
        return

    #Wrapper function to control all trading
    def trade(self, board):
        for r1, r1_amount in self.resources.items():
            if(r1_amount >= 6): #heuristic to trade if a player has more than 5 of a particular resource
                for r2, r2_amount in self.resources.items():
                    if(r2_amount < 1):
                        self.trade_with_bank(r1, r2, board)
                        break

    
    #Choose which player to rob
    def choose_player_to_rob(self, board):
        '''Heuristic function to choose the player with maximum points.
        Choose hex with maximum other players, Avoid blocking own resource
        args: game board object
        returns: hex index and player to rob
        '''
        #Get list of robber spots
        robberHexDict = board.get_robber_spots()

        #Initialize fallback values in case no opponent can be robbed
        hexToRob_index = None
        playerToRob_hex = None

        #Choose a hexTile with maximum adversary settlements
        maxHexScore = -float('inf') #Keep only the best hex to rob
        for hex_ind, hexTile in robberHexDict.items():
            #Extract all 6 vertices of this hexTile
            vertexList = polygon_corners(board.flat, hexTile.hex)

            hexScore = 0 #Heuristic score for hexTile
            playerToRob_VP = 0
            playerToRob = None
            for vertex in vertexList:
                playerAtVertex = board.boardGraph[vertex].state['Player']
                if playerAtVertex == self:
                    hexScore -= self.victoryPoints
                elif playerAtVertex != None: #There is an adversary on this vertex
                    hexScore += playerAtVertex.visibleVictoryPoints
                    #Find strongest other player at this hex, provided player has resources
                    if playerAtVertex.visibleVictoryPoints >= playerToRob_VP and sum(playerAtVertex.resources.values()) > 0:
                        playerToRob_VP = playerAtVertex.visibleVictoryPoints
                        playerToRob = playerAtVertex
                else:
                    pass

            if hexScore >= maxHexScore and playerToRob is not None:
                hexToRob_index = hex_ind
                playerToRob_hex = playerToRob
                maxHexScore = hexScore

        #If no suitable opponent found, choose a random hex and don't rob
        if hexToRob_index is None:
            hexToRob_index = np.random.choice(list(robberHexDict.keys()))
            return hexToRob_index, None

        return hexToRob_index, playerToRob_hex


    def heuristic_move_robber(self, board):
        '''Function to control heuristic AI robber
        Calls the choose_player_to_rob and move_robber functions
        args: board object
        '''
        #Get the best hex and player to rob
        hex_i, playerRobbed = self.choose_player_to_rob(board)

        #Move the robber, printing a message if no player was robbed
        if playerRobbed is None:
            print("No suitable opponent found. Robber moved without stealing")
        self.move_robber(hex_i, board, playerRobbed)

        return


    def heuristic_play_dev_card(self, board, game=None):
        """Play a development card using simple heuristics.

        Parameters
        ----------
        board : ``catanBoard``
            Current game board.
        game : game instance, optional
            Needed for actions that modify global game state such as
            checking largest army or longest road. ``None`` is allowed
            for testing.
        """

        if self.devCardPlayedThisTurn:
            return False

        # List available development cards excluding VP cards
        available = {
            k: v for k, v in self.devCards.items() if k != "VP" and v > 0
        }
        if not available:
            return False

        # --------------------------------------------------
        # Knight card: play if robber is blocking one of our tiles or
        # if we have spare knights to try for Largest Army
        # --------------------------------------------------
        if self.devCards["KNIGHT"] > 0:
            robber_blocking = False
            for v in (
                self.buildGraph["SETTLEMENTS"] + self.buildGraph["CITIES"]
            ):
                for h in board.boardGraph[v].adjacentHexList:
                    if board.hexTileDict[h].robber:
                        robber_blocking = True
                        break
                if robber_blocking:
                    break

            if robber_blocking or self.devCards["KNIGHT"] > 1:
                self.devCards["KNIGHT"] -= 1
                self.devCardPlayedThisTurn = True
                self.knightsPlayed += 1
                self.heuristic_move_robber(board)
                if game is not None:
                    game.check_largest_army(self)
                return True

        # --------------------------------------------------
        # Road Builder: attempt to expand for free if any road is available
        # --------------------------------------------------
        if self.devCards["ROADBUILDER"] > 0:
            potential = board.get_potential_roads(self)
            if potential:
                self.devCards["ROADBUILDER"] -= 1
                self.devCardPlayedThisTurn = True
                for _ in range(2):
                    potential = board.get_potential_roads(self)
                    if not potential:
                        break
                    edge = list(potential.keys())[np.random.randint(0, len(potential))]
                    self.build_road(edge[0], edge[1], board, free=True)
                if game is not None:
                    game.check_longest_road(self)
                return True

        # --------------------------------------------------
        # Year of Plenty: grab resources needed for settlement/city
        # --------------------------------------------------
        if self.devCards["YEAROFPLENTY"] > 0:
            needed = self.resources_needed_for_city()
            settle_need = self.resources_needed_for_settlement()
            for r, a in settle_need.items():
                if r not in needed:
                    needed[r] = a
            if needed:
                self.devCards["YEAROFPLENTY"] -= 1
                self.devCardPlayedThisTurn = True
                choices = list(needed.keys())
                # Pick up to two different needed resources
                r1 = choices[0]
                if board.withdraw_resource(r1):
                    self.resources[r1] += 1
                r2 = choices[1] if len(choices) > 1 else choices[0]
                if board.withdraw_resource(r2):
                    self.resources[r2] += 1
                return True

        # --------------------------------------------------
        # Monopoly: take the most common resource among opponents
        # --------------------------------------------------
        if self.devCards["MONOPOLY"] > 0 and game is not None:
            counts = {r: 0 for r in self.resources.keys()}
            for p in list(game.playerQueue.queue):
                if p == self:
                    continue
                for r, amt in p.resources.items():
                    counts[r] += amt
            resource = max(counts, key=counts.get)
            if counts[resource] > 0:
                self.devCards["MONOPOLY"] -= 1
                self.devCardPlayedThisTurn = True
                for p in list(game.playerQueue.queue):
                    if p == self:
                        continue
                    amt = p.resources[resource]
                    p.resources[resource] = 0
                    self.resources[resource] += amt
                return True

        return False


    def resources_needed_for_settlement(self):
        '''Function to return the resources needed for a settlement
        args: player object - use self.resources
        returns: list of resources needed for a settlement
        '''
        resourcesNeededDict = {}
        for resourceName in self.resources.keys():
            if resourceName != 'ORE' and self.resources[resourceName] == 0:
                resourcesNeededDict[resourceName] = 1

        return resourcesNeededDict


    def resources_needed_for_city(self):
        '''Function to return the resources needed for a city
        args: player object - use self.resources
        returns: list of resources needed for a city
        '''
        resourcesNeededDict = {}
        if self.resources['ORE'] < 3:
            resourcesNeededDict['ORE'] = 3 - self.resources['ORE']

        if self.resources['WHEAT'] < 2:
            resourcesNeededDict['WHEAT'] = 2 - self.resources['WHEAT']

        return resourcesNeededDict

    def heuristic_discard(self, board):
        '''Function for the AI to choose a set of cards to discard upon rolling a 7
        '''
        maxCards = 7
        totalResourceCount = sum(self.resources.values())

        if totalResourceCount > maxCards:
            numCardsToDiscard = int(totalResourceCount/2)
            print("\nAI Player {} has {} cards and discards {} cards".format(self.name, totalResourceCount, numCardsToDiscard))

            for i in range(numCardsToDiscard):
                resourceToDiscard = max(self.resources, key=lambda r: self.resources[r])
                self.resources[resourceToDiscard] -= 1
                board.deposit_resource(resourceToDiscard)
                print("AI {} discarded a {}".format(self.name, resourceToDiscard))
        else:
            print("\nAI Player {} has {} cards and does not need to discard".format(self.name, totalResourceCount))

        return

    #Function to propose a trade -> give r1 and get r2
    #Propose a trade as a dictionary with {r1:amt_1, r2: amt_2} specifying the trade
    #def propose_trade_with_players(self):
    

    #Function to accept/reject trade - return True if accept
    #def accept_trade(self, r1_dict, r2_dict):
        

    #Function to find best action - based on gamestate
    def get_action(self):
        return

    #Function to execute the player's action
    def execute_action(self):
        return




