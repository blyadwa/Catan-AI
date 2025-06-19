#Settlers of Catan
#Gameplay class with pygame

from board import *
from gameView import *
from player import *
from heuristicAIPlayer import *
import queue
import numpy as np
import sys, pygame

#Catan gameplay class definition
class catanGame():
    #Create new gameboard
    def __init__(self):
        print("Initializing Settlers of Catan Board...")
        self.board = catanBoard()

        #Game State variables
        self.gameOver = False
        self.maxPoints = 10
        self.numPlayers = 0

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

        #Run functions to view board and vertex graph
        #self.board.printGraph()

        #Functiont to go through initial set up
        self.build_initial_settlements()

        #Display initial board
        self.boardView.displayGameScreen()
    

    #Function to initialize players + build initial settlements for players
    def build_initial_settlements(self):
        #Initialize new players with names and colors. Ask whether each
        #participant is human or AI and only create AI players when selected.
        playerColors = ['black', 'darkslateblue', 'magenta4', 'orange1']
        players = []
        for i in range(self.numPlayers):
            playerName = input("Enter Player {} name: ".format(i + 1))
            ai_choice = ''
            while ai_choice.lower() not in ['y', 'n']:
                ai_choice = input(
                    "Is {} an AI player? (y/n): ".format(playerName)
                ).strip().lower()

            if ai_choice == 'y':
                new_player = heuristicAIPlayer(playerName, playerColors[i])
                new_player.updateAI()
            else:
                new_player = player(playerName, playerColors[i])

            players.append(new_player)

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

        self.boardView.displayGameScreen() #display the initial gameScreen
        print("Displaying Initial GAMESCREEN!")

        #Build Settlements and roads of each player forwards
        for player_i in playerList: 
            if(player_i.isAI):
                player_i.initial_setup(self.board, self)
            
            else:
                self.build(player_i, 'SETTLE')
                self.boardView.displayGameScreen()
                
                self.build(player_i, 'ROAD')
                self.boardView.displayGameScreen()
        
        #Build Settlements and roads of each player reverse
        playerList.reverse()
        for player_i in playerList: 
            if(player_i.isAI):
                player_i.initial_setup(self.board, self)
                self.boardView.displayGameScreen()

            else:
                self.build(player_i, 'SETTLE')
                self.boardView.displayGameScreen()

                self.build(player_i, 'ROAD')
                self.boardView.displayGameScreen()

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

        self.gameSetup = False

        return


    #Generic function to handle all building in the game - interface with gameView
    def build(self, player, build_flag, free=False):
        if(build_flag == 'ROAD'): #Show screen with potential roads
            if(self.gameSetup):
                potentialRoadDict = self.board.get_setup_roads(player)
            else:
                potentialRoadDict = self.board.get_potential_roads(player)

            roadToBuild = self.boardView.buildRoad_display(player, potentialRoadDict)
            if(roadToBuild != None):
                player.build_road(roadToBuild[0], roadToBuild[1], self.board,
                                 free=(self.gameSetup or free))

            
        if(build_flag == 'SETTLE'): #Show screen with potential settlements
            if(self.gameSetup):
                potentialVertexDict = self.board.get_setup_settlements(player)
            else:
                potentialVertexDict = self.board.get_potential_settlements(player)
            
            vertexSettlement = self.boardView.buildSettlement_display(player, potentialVertexDict)
            if(vertexSettlement != None):
                built = player.build_settlement(vertexSettlement, self.board,
                                               free=(self.gameSetup or free))
                if built:
                    for p in list(self.playerQueue.queue):
                        self.check_longest_road(p)

        if(build_flag == 'CITY'): 
            potentialCityVertexDict = self.board.get_potential_cities(player)
            vertexCity = self.boardView.buildSettlement_display(player, potentialCityVertexDict)
            if(vertexCity != None):
                built = player.build_city(vertexCity, self.board)
                if built:
                    for p in list(self.playerQueue.queue):
                        self.check_longest_road(p)


    #Wrapper Function to handle robber functionality
    def robber(self, player):
        potentialRobberDict = self.board.get_robber_spots()
        print("Move Robber!")

        hex_i, playerRobbed = self.boardView.moveRobber_display(player, potentialRobberDict)
        player.move_robber(hex_i, self.board, playerRobbed)


    #Function to roll dice 
    def rollDice(self):
        dice_1 = np.random.randint(1,7)
        dice_2 = np.random.randint(1,7)
        diceRoll = dice_1 + dice_2
        print("Dice Roll = ", diceRoll, "{", dice_1, dice_2, "}")

        self.boardView.displayDiceRoll(diceRoll)

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

                print(
                    "Player:{}, Resources:{}, Points: {}".format(
                        player_i.name,
                        player_i.resources,
                        player_i.visibleVictoryPoints,
                    )
                )
                print('MaxRoadLength:{}, LongestRoad:{}\n'.format(player_i.maxRoadLength, player_i.longestRoadFlag))
        
        #Logic for a 7 roll
        else:
            #Implement discarding cards for each player
            for player_i in list(self.playerQueue.queue):
                if player_i.isAI:
                    print("AI discarding resources...")
                    player_i.heuristic_discard(self.board)
                else:
                    player_i.discardResources(self.board)

            #Logic for robber
            if(currentPlayer.isAI):
                print("AI using heuristic robber...")
                currentPlayer.heuristic_move_robber(self.board)
            else:
                self.robber(currentPlayer)
                self.boardView.displayGameScreen()#Update back to original gamescreen


    #function to check if a player has the longest road - after building latest road
    def check_longest_road(self, player_i):
        """Evaluate and assign the Longest Road bonus."""
        players = list(self.playerQueue.queue)

        max_len = max(p.maxRoadLength for p in players)
        contenders = [p for p in players if p.maxRoadLength == max_len and max_len >= 5]

        current_holder = None
        for p in players:
            if p.longestRoadFlag:
                current_holder = p
                break

        if len(contenders) != 1:  # No single player qualifies
            if current_holder is not None:
                current_holder.longestRoadFlag = False
                current_holder.victoryPoints -= 2
                current_holder.update_visible_vp()
            # Reset flags for any erroneous extra holders
            for p in players:
                if p != current_holder:
                    p.longestRoadFlag = False
            return

        winner = contenders[0]
        if current_holder == winner:
            return  # nothing to update

        # Remove bonus from previous holder if needed
        if current_holder is not None:
            current_holder.longestRoadFlag = False
            current_holder.victoryPoints -= 2
            current_holder.update_visible_vp()

        # Assign to the winner
        for p in players:
            if p != winner:
                p.longestRoadFlag = False

        if not winner.longestRoadFlag:
            winner.longestRoadFlag = True
            winner.victoryPoints += 2
            winner.update_visible_vp()
            prev = f"from Player {current_holder.name}" if current_holder else ''
            print(f"Player {winner.name} takes Longest Road {prev}")

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

        while (self.gameOver == False):

            #Loop for each player's turn -> iterate through the player queue
            for currPlayer in self.playerQueue.queue:

                print("---------------------------------------------------------------------------")
                print("Current Player:", currPlayer.name)

                turnOver = False #boolean to keep track of turn
                diceRolled = False  #Boolean for dice roll status
                
                #Update Player's dev card stack with dev cards drawn in previous turn and reset devCardPlayedThisTurn
                currPlayer.updateDevCards()
                currPlayer.devCardPlayedThisTurn = False

                while(turnOver == False):

                    # AI logic
                    if(currPlayer.isAI):
                        # Optionally play a development card before rolling
                        currPlayer.heuristic_play_dev_card(self.board, self)

                        # Roll Dice
                        diceNum = self.rollDice()
                        diceRolled = True
                        self.update_playerResources(diceNum, currPlayer)

                        # Perform regular turn actions
                        currPlayer.move(self.board, self)
                        #Check if AI player gets longest road/largest army and update Victory points
                        self.check_longest_road(currPlayer)
                        self.check_largest_army(currPlayer)
                        print(
                            "Player:{}, Resources:{}, Points: {}".format(
                                currPlayer.name,
                                currPlayer.resources,
                                currPlayer.visibleVictoryPoints,
                            )
                        )
                        
                        self.boardView.displayGameScreen()#Update back to original gamescreen
                        turnOver = True

                    else: #Game loop for human players
                        for e in pygame.event.get(): #Get player actions/in-game events
                            #print(e)
                            if e.type == pygame.QUIT:
                                sys.exit(0)

                            #Check mouse click in rollDice
                            if(e.type == pygame.MOUSEBUTTONDOWN):
                                #Check if player rolled the dice
                                if(self.boardView.rollDice_button.collidepoint(e.pos)):
                                    if(diceRolled == False): #Only roll dice once
                                        diceNum = self.rollDice()
                                        diceRolled = True
                                        
                                        self.boardView.displayDiceRoll(diceNum)
                                        #Code to update player resources with diceNum
                                        self.update_playerResources(diceNum, currPlayer)

                                #Check if player wants to build road
                                if(self.boardView.buildRoad_button.collidepoint(e.pos)):
                                    #Code to check if road is legal and build
                                    if(diceRolled == True): #Can only build after rolling dice
                                        self.build(currPlayer, 'ROAD')
                                        self.boardView.displayGameScreen()#Update back to original gamescreen

                                        #Check if player gets longest road and update Victory points
                                        self.check_longest_road(currPlayer)
                                        #Show updated points and resources  
                                        print(
                                            "Player:{}, Resources:{}, Points: {}".format(
                                                currPlayer.name,
                                                currPlayer.resources,
                                                currPlayer.visibleVictoryPoints,
                                            )
                                        )

                                #Check if player wants to build settlement
                                if(self.boardView.buildSettlement_button.collidepoint(e.pos)):
                                    if(diceRolled == True): #Can only build settlement after rolling dice
                                        self.build(currPlayer, 'SETTLE')
                                        self.boardView.displayGameScreen()#Update back to original gamescreen
                                        #Show updated points and resources  
                                        print(
                                            "Player:{}, Resources:{}, Points: {}".format(
                                                currPlayer.name,
                                                currPlayer.resources,
                                                currPlayer.visibleVictoryPoints,
                                            )
                                        )

                                #Check if player wants to build city
                                if(self.boardView.buildCity_button.collidepoint(e.pos)):
                                    if(diceRolled == True): #Can only build city after rolling dice
                                        self.build(currPlayer, 'CITY')
                                        self.boardView.displayGameScreen()#Update back to original gamescreen
                                        #Show updated points and resources  
                                        print(
                                            "Player:{}, Resources:{}, Points: {}".format(
                                                currPlayer.name,
                                                currPlayer.resources,
                                                currPlayer.visibleVictoryPoints,
                                            )
                                        )

                                #Check if player wants to draw a development card
                                if(self.boardView.devCard_button.collidepoint(e.pos)):
                                    if(diceRolled == True): #Can only draw devCard after rolling dice
                                        currPlayer.draw_devCard(self.board)
                                        #Show updated points and resources  
                                        print(
                                            "Player:{}, Resources:{}, Points: {}".format(
                                                currPlayer.name,
                                                currPlayer.resources,
                                                currPlayer.visibleVictoryPoints,
                                            )
                                        )
                                        print('Available Dev Cards:', currPlayer.get_public_dev_cards())

                                #Check if player wants to play a development card - can play devCard whenever after rolling dice
                                if(self.boardView.playDevCard_button.collidepoint(e.pos)):
                                        currPlayer.play_devCard(self)
                                        self.boardView.displayGameScreen()#Update back to original gamescreen
                                        
                                        #Check for Largest Army and longest road
                                        self.check_largest_army(currPlayer)
                                        self.check_longest_road(currPlayer)
                                        #Show updated points and resources  
                                        print(
                                            "Player:{}, Resources:{}, Points: {}".format(
                                                currPlayer.name,
                                                currPlayer.resources,
                                                currPlayer.visibleVictoryPoints,
                                            )
                                        )
                                        print('Available Dev Cards:', currPlayer.get_public_dev_cards())

                                #Check if player wants to trade with the bank
                                if(self.boardView.tradeBank_button.collidepoint(e.pos)):
                                    if(diceRolled == True):
                                        currPlayer.initiate_trade(self, 'BANK')
                                        #Show updated points and resources
                                        print(
                                            "Player:{}, Resources:{}, Points: {}".format(
                                                currPlayer.name,
                                                currPlayer.resources,
                                                currPlayer.visibleVictoryPoints,
                                            )
                                        )
                                    else:
                                        print("You must roll the dice before trading with the bank.")
                                
                                #Check if player wants to trade with another player
                                if(self.boardView.tradePlayers_button.collidepoint(e.pos)):
                                    if(diceRolled == True):
                                        currPlayer.initiate_trade(self, 'PLAYER')
                                        #Show updated points and resources
                                        print(
                                            "Player:{}, Resources:{}, Points: {}".format(
                                                currPlayer.name,
                                                currPlayer.resources,
                                                currPlayer.visibleVictoryPoints,
                                            )
                                        )
                                    else:
                                        print("You must roll the dice before trading with other players.")

                                #Check if player wants to end turn
                                if(self.boardView.endTurn_button.collidepoint(e.pos)):
                                    if(diceRolled == True): #Can only end turn after rolling dice
                                        print("Ending Turn!")
                                        turnOver = True  #Update flag to nextplayer turn

                    #Update the display
                    #self.displayGameScreen(None, None)
                    pygame.display.update()
                    
                    #Check if game is over
                    if currPlayer.victoryPoints >= self.maxPoints:
                        self.gameOver = True
                        self.turnOver = True
                        print("====================================================")
                        print("PLAYER {} WINS!".format(currPlayer.name))
                        print("Exiting game in 10 seconds...")
                        break

                if(self.gameOver):
                    startTime = pygame.time.get_ticks()
                    runTime = 0
                    while(runTime < 10000): #10 second delay prior to quitting
                        runTime = pygame.time.get_ticks() - startTime

                    break
                    
                

#Initialize new game and run
if __name__ == '__main__':
    newGame = catanGame()
    newGame.playCatan()
