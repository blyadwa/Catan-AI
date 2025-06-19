#Settlers of Catan
#Gameplay class with pygame with AI players

from board import *
from gameView import *
from player import *
from heuristicAIPlayer import *
import queue
import numpy as np
import sys, pygame
import matplotlib.pyplot as plt

#Class to implement an only AI
class catanAIGame():
    #Create new gameboard
    def __init__(self):
        print("Initializing Settlers of Catan with only AI Players...")
        self.board = catanBoard()

        #Game State variables
        self.gameOver = False
        self.maxPoints = 10
        self.numPlayers = 0

        #Dictionary to keep track of dice statistics
        self.diceStats = {2:0, 3:0, 4:0, 5:0, 6:0, 7:0, 8:0, 9:0, 10:0, 11:0, 12:0}
        self.diceStats_list = []

        while(self.numPlayers not in [3,4]): #Only accept 3 and 4 player games
            try:
                self.numPlayers = int(input("Enter Number of Players (3 or 4):"))
            except:
                print("Please input a valid number")

        print("Initializing game with {} players...".format(self.numPlayers))
        print("Note that Player 1 goes first, Player 2 second and so forth.")
        
        #Initialize blank player queue and initial set up of roads + settlements
        self.playerQueue = queue.Queue(self.numPlayers)
        self.gameSetup = True #Boolean to take care of setup phase

        #Initialize boardview object
        self.boardView = catanGameView(self.board, self)

        #Functiont to go through initial set up
        self.build_initial_settlements()
        self.playCatan()

        #Plot diceStats histogram
        plt.hist(self.diceStats_list, bins = 11)
        plt.show()

        return None
    

    #Function to initialize players + build initial settlements for players
    def build_initial_settlements(self):
        #Initialize new players with names and colors
        playerColors = ['black', 'darkslateblue', 'magenta4', 'orange1']
        players = []
        for i in range(self.numPlayers):
            playerNameInput = input("Enter AI Player {} name: ".format(i+1))
            newPlayer = heuristicAIPlayer(playerNameInput, playerColors[i])
            newPlayer.updateAI()
            players.append(newPlayer)

        contenders = players[:]
        while True:
            highest_roll = -1
            highest_players = []
            for p in contenders:
                roll = np.random.randint(1,7) + np.random.randint(1,7)
                print(f"{p.name} rolls {roll} for starting order")
                if roll > highest_roll:
                    highest_roll = roll
                    highest_players = [p]
                elif roll == highest_roll:
                    highest_players.append(p)
            if len(highest_players) == 1:
                start_player = highest_players[0]
                break
            print("Tie for highest roll. Rolling again...")
            contenders = highest_players

        self.playerQueue.put(start_player)
        for p in players:
            if p != start_player:
                self.playerQueue.put(p)

        playerList = list(self.playerQueue.queue)

        #Build Settlements and roads of each player forwards
        for player_i in playerList:
            player_i.initial_setup(self.board, self)
            pygame.event.pump()
            self.boardView.displayGameScreen()
            pygame.time.delay(1000)


        #Build Settlements and roads of each player reverse
        playerList.reverse()
        for player_i in playerList:
            player_i.initial_setup(self.board, self)
            pygame.event.pump()
            self.boardView.displayGameScreen()
            pygame.time.delay(1000)
            
            print("Player {} starts with {} resources".format(player_i.name, len(player_i.setupResources)))

            #Initial resource generation
            #check each adjacent hex to latest settlement
            for adjacentHex in self.board.boardGraph[player_i.buildGraph['SETTLEMENTS'][-1]].adjacentHexList:
                resourceGenerated = self.board.hexTileDict[adjacentHex].resource.type
                if resourceGenerated != 'DESERT':
                    self.board.withdraw_resource(resourceGenerated)
                    player_i.resources[resourceGenerated] += 1
                    print(
                        "{} collects 1 {} from Settlement".format(
                            player_i.name, resourceGenerated))
        
        pygame.time.delay(5000)
        self.gameSetup = False


    #Function to roll dice 
    def rollDice(self):
        dice_1 = np.random.randint(1,7)
        dice_2 = np.random.randint(1,7)
        diceRoll = dice_1 + dice_2
        print("Dice Roll = ", diceRoll, "{", dice_1, dice_2, "}")

        return diceRoll

    #Function to update resources for all players
    def update_playerResources(self, diceRoll, currentPlayer):
        if(diceRoll != 7): #Collect resources if not a 7
            #First get the hex or hexes corresponding to diceRoll
            hexResourcesRolled = self.board.getHexResourceRolled(diceRoll)

            # Track resource demand for each player
            demand = {}
            for player_i in list(self.playerQueue.queue):
                demand[player_i] = {r: 0 for r in self.board.resourceBank.keys()}

                #Check each settlement the player has
                for settlementCoord in player_i.buildGraph['SETTLEMENTS']:
                    for adjacentHex in self.board.boardGraph[settlementCoord].adjacentHexList:
                        if(adjacentHex in hexResourcesRolled and self.board.hexTileDict[adjacentHex].robber == False):
                            resourceGenerated = self.board.hexTileDict[adjacentHex].resource.type
                            demand[player_i][resourceGenerated] += 1

                #Check each City the player has
                for cityCoord in player_i.buildGraph['CITIES']:
                    for adjacentHex in self.board.boardGraph[cityCoord].adjacentHexList:
                        if(adjacentHex in hexResourcesRolled and self.board.hexTileDict[adjacentHex].robber == False):
                            resourceGenerated = self.board.hexTileDict[adjacentHex].resource.type
                            demand[player_i][resourceGenerated] += 2

            # Allocate resources based on bank supply
            allocation = {p: {r: 0 for r in self.board.resourceBank.keys()} for p in demand}
            for resource in self.board.resourceBank.keys():
                total_demand = sum(d[resource] for d in demand.values())
                if total_demand == 0:
                    continue
                players_requesting = [p for p in demand if demand[p][resource] > 0]
                supply = self.board.resourceBank[resource]

                if supply >= total_demand:
                    for p in players_requesting:
                        allocation[p][resource] = demand[p][resource]
                    self.board.withdraw_resource(resource, total_demand)
                elif len(players_requesting) == 1 and supply > 0:
                    p = players_requesting[0]
                    allocation[p][resource] = min(supply, demand[p][resource])
                    self.board.withdraw_resource(resource, allocation[p][resource])
                # If supply is insufficient and more than one player wants it,
                # nobody gets any. No withdrawal in this case.

            # Give players their allocated resources
            for player_i in list(self.playerQueue.queue):
                for resource, qty in allocation[player_i].items():
                    if qty:
                        player_i.resources[resource] += qty
                        print("{} collects {} {}".format(player_i.name, qty, resource))

                print("Player:{}, Resources:{}, Points: {}".format(player_i.name, player_i.resources, player_i.victoryPoints))
                print('MaxRoadLength:{}, Longest Road:{}\n'.format(player_i.maxRoadLength, player_i.longestRoadFlag))
        
        else:
            print("AI using heuristic robber...")
            currentPlayer.heuristic_move_robber(self.board)


    #function to check if a player has the longest road - after building latest road
    def check_longest_road(self, player_i):
        if(player_i.maxRoadLength >= 5): #Only eligible if road length is at least 5
            longestRoad = True
            for p in list(self.playerQueue.queue):
                if(p.maxRoadLength >= player_i.maxRoadLength and p != player_i): #Check if any other players have a longer road
                    longestRoad = False
            
            if(longestRoad and player_i.longestRoadFlag == False): #if player_i takes longest road and didn't already have longest road
                #Set previous players flag to false and give player_i the longest road points
                prevPlayer = ''
                for p in list(self.playerQueue.queue):
                    if(p.longestRoadFlag):
                        p.longestRoadFlag = False
                        p.victoryPoints -= 2
                        p.update_visible_vp()
                        prevPlayer = 'from Player ' + p.name
    
                player_i.longestRoadFlag = True
                player_i.victoryPoints += 2
                player_i.update_visible_vp()

                print("Player {} takes Longest Road {}".format(player_i.name, prevPlayer))

    #function to check if a player has the largest army - after playing latest knight
    def check_largest_army(self, player_i):
        if(player_i.knightsPlayed >= 3): #Only eligible if at least 3 knights are player
            largestArmy = True
            for p in list(self.playerQueue.queue):
                if(p.knightsPlayed >= player_i.knightsPlayed and p != player_i): #Check if any other players have more knights played
                    largestArmy = False
            
            if(largestArmy and player_i.largestArmyFlag == False): #if player_i takes largest army and didn't already have it
                #Set previous players flag to false and give player_i the largest points
                prevPlayer = ''
                for p in list(self.playerQueue.queue):
                    if(p.largestArmyFlag):
                        p.largestArmyFlag = False
                        p.victoryPoints -= 2
                        p.update_visible_vp()
                        prevPlayer = 'from Player ' + p.name
    
                player_i.largestArmyFlag = True
                player_i.victoryPoints += 2
                player_i.update_visible_vp()

                print("Player {} takes Largest Army {}".format(player_i.name, prevPlayer))



    #Function that runs the main game loop with all players and pieces
    def playCatan(self):
        #self.board.displayBoard() #Display updated board
        numTurns = 0
        while (self.gameOver == False):
            #Loop for each player's turn -> iterate through the player queue
            for currPlayer in self.playerQueue.queue:
                numTurns += 1
                print("---------------------------------------------------------------------------")
                print("Current Player:", currPlayer.name)

                turnOver = False #boolean to keep track of turn
                diceRolled = False  #Boolean for dice roll status
                
                #Update Player's dev card stack with dev cards drawn in previous turn and reset devCardPlayedThisTurn
                currPlayer.updateDevCards()
                currPlayer.devCardPlayedThisTurn = False

                while(turnOver == False):

                    #TO-DO: Add logic for AI Player to move
                    #TO-DO: Add option of AI Player playing a dev card prior to dice roll
                    
                    #Roll Dice and update player resources and dice stats
                    pygame.event.pump()
                    diceNum = self.rollDice()
                    diceRolled = True
                    self.update_playerResources(diceNum, currPlayer)
                    self.diceStats[diceNum] += 1
                    self.diceStats_list.append(diceNum)

                    currPlayer.move(self.board, self) #AI Player makes all its moves
                    #Check if AI player gets longest road and update Victory points
                    self.check_longest_road(currPlayer)
                    #Also update Largest Army status in case a knight was played
                    self.check_largest_army(currPlayer)
                    print("Player:{}, Resources:{}, Points: {}".format(currPlayer.name, currPlayer.resources, currPlayer.victoryPoints))
                    
                    self.boardView.displayGameScreen()#Update back to original gamescreen
                    pygame.time.delay(300)
                    turnOver = True
                    
                    #Check if game is over
                    if currPlayer.victoryPoints >= self.maxPoints:
                        self.gameOver = True
                        self.turnOver = True
                        print("====================================================")
                        print("PLAYER {} WINS IN {} TURNS!".format(currPlayer.name, int(numTurns/4)))
                        print(self.diceStats)
                        print("Exiting game in 10 seconds...")
                        pygame.time.delay(10000)
                        break

                if(self.gameOver):
                    startTime = pygame.time.get_ticks()
                    runTime = 0
                    while(runTime < 5000): #5 second delay prior to quitting
                        runTime = pygame.time.get_ticks() - startTime

                    break
                                   

#Initialize new game and run
if __name__ == '__main__':
    newGame_AI = catanAIGame()
