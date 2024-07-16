import sqlite3
import datetime
import json
import random 
import datetime

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

cooldown_bypass = True

def createRepository():
    cursor.execute("CREATE TABLE IF NOT EXISTS cooldown(id INT PRIMARY KEY, last_daily TEXT, last_quest TEXT )")
    cursor.execute("CREATE TABLE IF NOT EXISTS quests(id INT PRIMARY KEY,quest1 TEXT, quest2 TEXT, quest3 TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS users(id INT PRIMARY KEY, points REAL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS stocks(id INT PRIMARY KEY, stock_dicts TEXT, transactions TEXT)")

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

async def insertNewUserIfNotExists(id:int):
    cursor.execute("SELECT * FROM users WHERE id=?",(id,))
    if(cursor.fetchone() is None):        
        cursor.execute("INSERT INTO users VALUES(?,?)",(id,0))
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
        await updateQuests(id, questDict["Buy Stock"], amount)
    elif (action=="Sell"):
        await updatePoints(id, stock_dict["bid"]*amount)
        newAmountOfStock = userData[0][ticker]-amount
        if (newAmountOfStock>0):
            userData[0][ticker] = newAmountOfStock 
        else:
            del userData[0][ticker]
        price = stock_dict["bid"]
        
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

async def updatePoints(id:int, change:int):
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
        