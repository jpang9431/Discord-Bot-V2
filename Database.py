import sqlite3
import datetime
import json
import random 
import datetime
import yfinance as yf

globalConnection = sqlite3.connect("global.db")
connection = sqlite3.connect("users.db")
cursor = connection.cursor()

secertFile = open("config.json")
fileData = json.load(secertFile)

houseId = fileData["house_id"]

format = "%Y-%d-%m"

default_date = datetime.datetime(2024,1,1).strftime(format)

#quest
quests = {
    0:"Claim the daily reward ? time(s): */?",
    1:"Sell ? stock(s): */?",
    2:"Buy ? stock(s): */?"
}

questDict = {
    "Daily" : 0,
    "Sell Stock" : 1,
    "Buy Stock" : 2
}

cooldown_bypass = False

globalCursor = globalConnection.cursor()

async def calcStockValue(data):
    total = 0
    for key, value in data.items():
        info = yf.Ticker(key).info
        total += value*info["bid"]
    return total

async def updateLeaderBoard():
    cursor.execute("SELECT stock_dicts, id FROM stocks")
    stockData = cursor.fetchall()
    count = 0
    for row in stockData:
        amount = round(await calcStockValue(json.loads(row[0])), 2)
        await updateTotalAndStock(row[1],amount)
    cursor.execute("SELECT username, total, points, stock_value, id FROM users ORDER BY total DESC")
    users = cursor.fetchall()
    userNames = ""
    totals = ""
    pointsAndStocks = ""
    for row in users:
        count += 1
        userNames += str(count)+"."+row[0]+"\n"
        totals += str(row[1])+"\n"
        pointsAndStocks += str(row[2])+"|"+str(row[3])+"\n"
        cursor.execute("UPDATE users SET placement=? WHERE id=?",(count,row[4]))
        connection.commit()
    leaderBoard = json.dumps([userNames, totals, pointsAndStocks])
    globalCursor.execute("UPDATE globalData SET leaderboard=?, lastUpdate=?",(leaderBoard,str(datetime.datetime.now())))
    globalConnection.commit()
    
async def getLastUpdate():
    globalCursor.execute("SELECT lastUpdate FROM globalData")    
    return globalCursor.fetchone()[0]

async def getLeaderBoard():
    globalCursor.execute("SELECT leaderboard FROM globalData")
    return globalCursor.fetchone()
    
async def updateTotalAndStock(id:int, stockAmount:int):
    total = round(await getPoints(id) + stockAmount,2)
    cursor.execute("UPDATE users SET stock_value=?, total=? WHERE id=?",(stockAmount, total, id))
    connection.commit()
    
async def getLeaderBoard():
    globalCursor.execute("SELECT leaderboard FROM globalData")
    return globalCursor.fetchone()[0]

async def getUserData(id:int):
    cursor.execute("SELECT placement, username, total, points, stock_value FROM users WHERE id=?",(id,))
    return cursor.fetchone()

async def getPostion(id:int):
    cursor.execute("SELECT placement FROM users WHERE id=?",(id,))

def createRepository():
    cursor.execute("CREATE TABLE IF NOT EXISTS cooldown(id INT PRIMARY KEY, last_daily TEXT, last_quest TEXT )")
    cursor.execute("CREATE TABLE IF NOT EXISTS quests(id INT PRIMARY KEY,quest1 TEXT, quest2 TEXT, quest3 TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS users(id INT PRIMARY KEY, points REAL, stock_value REAL, total REAL, username TEXT, placement INT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS stocks(id INT PRIMARY KEY, stock_dicts TEXT, transactions TEXT)")
    globalCursor.execute("CREATE TABLE IF NOT EXISTS globalData(leaderboard TEXT, users INT, lastUpdate TEXT)")
    globalCursor.execute("SELECT * FROM globalData")
    if(globalCursor.fetchone() is None):   
        globalCursor.execute("INSERT INTO globalData VALUES(?,?,?)",("",0,str(datetime.datetime.now())))
        globalConnection.commit()

async def resetDailyCooldown(id:int):
    date = datetime.datetime.today().strftime(format)
    cursor.execute("UPDATE cooldown SET last_daily=? WHERE id=?",(date,id))
    connection.commit()

async def checkDailyCooldown(id:int):
    cursor.execute("SELECT last_daily FROM cooldown WHERE id=?",(id,))
    timeDifference = (datetime.datetime.today() - datetime.datetime.strptime(cursor.fetchone()[0], format)).days
    return timeDifference>=1 or cooldown_bypass

async def checkQuestCooldown(id:int):
    cursor.execute("SELECT last_quest FROM cooldown WHERE id=?",(id,))
    timeDifference = (datetime.datetime.today() - datetime.datetime.strptime(cursor.fetchone()[0], format)).days
    return timeDifference>=1 or cooldown_bypass

async def resetQuestCooldown(id:int):
    date = datetime.datetime.today().strftime(format)
    cursor.execute("UPDATE cooldown SET last_quest=? WHERE id=?",(date,id))
    connection.commit()
    
async def updateQuests(id:int, quest_id:int, amount:int=1):
    cursor.execute("SELECT quest1, quest2, quest3 FROM quests WHERE id=?",(id,))
    quests = list(cursor.fetchone())
    for i in range(len(quests)):
        quest_dict = json.loads(quests[i])
        if (quest_dict["id"] == quest_id):
            quest_dict.update(progress=quest_dict["progress"]+amount)
            quests[i] = json.dumps(quest_dict)
    cursor.execute("UPDATE quests SET quest1 = ?, quest2 = ?, quest3 = ? WHERE id=?",(quests[0],quests[1],quests[2],id))
    connection.commit()
    
def getNewQuest():
    goal = random.randint(1,5)
    quest = {
        "id" : random.randint(0,2),
        "progress" : 0,
        "goal" : goal,
        "points" : goal*random.randint(1,5),
        "claimed" : False
    }
    return json.dumps(quest)

async def getQuests(id:int):
    cursor.execute("SELECT quest1, quest2, quest3 FROM quests WHERE id=?",(id,))
    quests = list(cursor.fetchone())
    for i in range(len(quests)):
        quest_dict = json.loads(quests[i])
        quests[i] = quest_dict
    return quests

async def resetQuests(id:int):
    cursor.execute("UPDATE quests SET quest1 = ?, quest2 = ?, quest3 = ? WHERE id=?",(getNewQuest(),getNewQuest(),getNewQuest(),id))
    connection.commit()

async def setNewQuets(id:int):
    cursor.execute("SELECT quest1, quest2, quest3 FROM quests WHERE id=?",(id,))
    quests = list(cursor.fetchone())
    for i in range(len(quests)):
        quest = json.loads(quests[i])
        if quest["progress"]>=quest["goal"]:
            quests[i] = getNewQuest()
    cursor.execute("UPDATE quests SET quest1 = ?, quest2 = ?, quest3 = ? WHERE id=?",(quests[0],quests[1],quests[2],id))
            
async def claimQuests(id:int):
    cursor.execute("SELECT quest1, quest2, quest3 FROM quests WHERE id=?",(id,))
    quests = cursor.fetchone()
    total_points = 0
    for i in range(len(quests)):
        quest_dict = json.loads(quests[i])
        if (quest_dict["progress"]>=quest_dict["goal"] and not quest_dict["claimed"]):
            total_points+=quest_dict["points"]
            quest_dict["claimed"] = True
    cursor.execute("UPDATE quests SET quest1 = ?, quest2 = ?, quest3 = ? WHERE id=?",(quests[0],quests[1],quests[2],id))
    connection.commit()
    return total_points

async def insertNewUserIfNotExists(id:int,name:str):
    cursor.execute("SELECT * FROM users WHERE id=?",(id,))
    if(cursor.fetchone() is None):
        globalCursor.execute("SELECT users FROM globalData")
        numUsers = globalCursor.fetchone()[0]
        numUsers+=1        
        globalCursor.execute("UPDATE globalData SET users = ? ",(numUsers,))
        globalConnection.commit()
        cursor.execute("INSERT INTO users VALUES(?,?,?,?,?,?)",(id,0,0,0,name,numUsers))
        cursor.execute("INSERT INTO cooldown VALUES(?,?,?)",(id,default_date,default_date))
        cursor.execute("INSERT INTO quests VALUES(?,?,?,?)",(id,getNewQuest(),getNewQuest(),getNewQuest()))
        cursor.execute("INSERT INTO stocks VALUES(?,?,?)",(id, "{}", "[]"))
        connection.commit()
        

async def updateCountingDict(dict, value:int, change:int):
    if (dict.get(value)==None):
        dict[value] = change
    else:
        dict[value] = dict[value]+change

async def getAmountOfStock(id:int, ticker:str):
    cursor.execute("SELECT stock_dicts FROM stocks WHERE id=?",(id,))
    data = cursor.fetchone()
    dictionary = json.loads(data[0])
    if (ticker in dictionary):
        return dictionary[ticker]
    else:
        return 0

async def getStocks(id:int):
    cursor.execute("SELECT stock_dicts FROM stocks WHERE id=?",(id,))
    data = cursor.fetchone()
    dictionary = json.loads(data[0])
    return dictionary

async def updateStockValue(id:int, value:float):
    cursor.execute("SELECT stock_value FROM users WHERE id=?",(id,))
    data = cursor.fetchone()[0]
    data += value
    data = round(data, 2)
    cursor.execute("UPDATE users SET stock_value = ? WHERE id = ?",(data, id))
    connection.commit()

async def setStockValue(id:int, value:float):
    cursor.execute("UPDATE users SET stock_value=? WHERE id=?",(value, id))
    connection.commit()

async def getStoredStockValue(id:int):
    cursor.execute("SELECT stock_value FROM users WHERE id=?",(id,))
    return round(cursor.fetchone()[0],2)

async def updateStock(id:int, stock_dict, action:str, amount:int):
    cursor.execute("SELECT * FROM stocks WHERE id=? ",(id,))
    userDataJSON = cursor.fetchone()
    userData = []
    price = 0
    ticker = stock_dict["underlyingSymbol"]
    for i in range(2):
        userData.append(json.loads(userDataJSON[i+1]))
    if (userData[0].get(ticker)==None):
        userData[0][ticker] = 0
    if (action=="Buy"):
        await updatePoints(id, stock_dict["ask"]*-1*amount)
        userData[0][ticker] = userData[0][ticker]+amount
        price = stock_dict["ask"]
        await updateStockValue(id, stock_dict["bid"]*amount)
        await updateQuests(id, questDict["Buy Stock"], amount)
    elif (action=="Sell"):
        await updatePoints(id, stock_dict["bid"]*amount)
        newAmountOfStock = userData[0][ticker]-amount
        if (newAmountOfStock>0):
            userData[0][ticker] = newAmountOfStock 
        else:
            del userData[0][ticker]
        price = stock_dict["bid"]
        await updateStockValue(id, stock_dict["bid"]*amount*-1)
        await updateQuests(id, questDict["Sell Stock"], amount)
    transaction = {
        "stock":stock_dict["underlyingSymbol"],
        "action": action,
        "price":price
    }
    userData[1].append(transaction)
    cursor.execute("UPDATE stocks SET stock_dicts =?, transactions=? WHERE id=?",(json.dumps(userData[0]), json.dumps(userData[1]),id))
    connection.commit()

async def getPoints(id:int):
    cursor.execute("SELECT points FROM users WHERE id=?",(id,))
    points = cursor.fetchone()
    return points[0]

async def updatePoints(id:int, change:float):
    cursor.execute("SELECT points FROM users WHERE id=?",(id,))
    points = cursor.fetchone()[0]
    points += change
    points = round(points, 2)
    cursor.execute("UPDATE users SET points = ? WHERE id=?",(points, id))
    connection.commit()
    return points

async def transferFromHouse(targetId:int, transferAmount:int):
    housePoints = await getPoints(houseId)
    if (housePoints<transferAmount):
        await updatePoints(houseId, housePoints*-1)
    else:
        await updatePoints(houseId, transferAmount*-1)
    await updatePoints(targetId, transferAmount)

async def transferPoints(sourceId:int, targetId:int, transferAmount:int):
    if (transferAmount<0):
        return "Error, transfer amount must be greater than or equal to zero"
    elif (getPoints(sourceId)<transferAmount):
        return "Error, you do not have anough points to transfer"
    else:
        await updatePoints(sourceId, transferAmount*-1)
        await updatePoints(targetId, transferAmount)
        return "? transfered "+transferAmount+" amount of points to ?"

