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

def createRepository():
    cursor.execute("CREATE TABLE IF NOT EXISTS cooldown(id INT PRIMARY KEY, last_daily TEXT, last_quest TEXT )")
    cursor.execute("CREATE TABLE IF NOT EXISTS quests(id INT PRIMARY KEY,quest1 TEXT, quest2 TEXT, quest3 TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS users(id INT PRIMARY KEY, points INT)")

def resetDailyCooldown(id:int):
    date = datetime.datetime.today.strftime(format)
    cursor.execute("UPDATE cooldown SET last_daily=? WHERE id=?",(date,id))
    connection.commit()

async def checkDailyCooldown(id:int):
    cursor.execute("SELECT last_daily FROM cooldown WHERE id=?",(id,))
    timeDifference = (datetime.datetime.today() - datetime.datetime.strptime(cursor.fetchone()[0], format)).days
    return timeDifference>=1

async def checkQuestCooldown(id:int):
    cursor.execute("SELECT last_quest FROM cooldown WHERE id=?",(id,))
    timeDifference = (datetime.datetime.today() - datetime.datetime.strptime(cursor.fetchone()[0], format)).days
    return timeDifference>=1

def resetQuestCooldown(id:int):
    date = datetime.datetime.today().strftime(format)
    cursor.execute("UPDATE cooldown SET last_quest=? WHERE id=?",(date,id))
    connection.commit()
    
def updateQuests(id:int, quest_id:int):
    cursor.execute("SELECT quest1, quest2, quest3 FROM quests WHERE id=?",(id,))
    quests = cursor.fetchone()
    for i in range(len(quests)):
        quest_dict = json.loads(quests[i])
        if (quest_dict["id"] == quest_id):
            quest_dict.update(progress=quest_dict["progress"]+1)
            quests[i] = json.dump(quest_dict)
    cursor.execute("UPDATE quests SET quest1 = ?, quest2 = ?, quest3 = ? WHERE id=?",(quests[0],quests[1],quests[2],id))
    connection.commit()
    
def getNewQuest():
    goal = random.randint(1,5)
    print(goal)
    quest = {
        "id" : random.randint(0,2),
        "progress" : 0,
        "goal" : goal,
        "points" : goal*random.randint(1,5)
    }
    return json.dumps(quest)

async def getQuests(id:int):
    cursor.execute("SELECT quest1, quest2, quest3 FROM quests WHERE id=?",(id,))
    quests = list(cursor.fetchone())
    for i in range(len(quests)):
        quest_dict = json.loads(quests[i])
        quests[i] = quest_dict
    return quests

def resetQuests(id:int):
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
            
def claimQuests(id:int):
    cursor.execute("SELECT quest1, quest2, quest3 FROM quests WHERE id=?",(id,))
    quests = cursor.fetchone()
    total_points = 0
    for i in range(len(quests)):
        quest_dict = json.loads(quests[i])
        if (quest_dict["progress"]>=quest_dict["goal"]):
            total_points+=quest_dict["points"]
            quests[i] = "None"
    cursor.execute("UPDATE quests SET quest1 = ?, quest2 = ?, quest3 = ? WHERE id=?",(quests[0],quests[1],quests[2],id))
    connection.commit()
    return total_points

def insertNewUserIfNotExists(id:int):
    cursor.execute("SELECT * FROM users WHERE id=?",(id,))
    if(cursor.fetchone() is None):        
        cursor.execute("INSERT INTO users VALUES(?,?)",(id,0))
        cursor.execute("INSERT INTO cooldown VALUES(?,?,?)",(id,default_date,default_date))
        cursor.execute("INSERT INTO quests VALUES(?,?,?,?)",(id,getNewQuest(),getNewQuest(),getNewQuest()))
        connection.commit()

async def getPoints(id:int):
    cursor.execute("SELECT points FROM users WHERE id=?",(id,))
    points = cursor.fetchone()
    return points[0]

def updatePoints(id:int, change:int):
    cursor.execute("SELECT points FROM users WHERE id=?",(id,))
    points = cursor.fetchone()[0]
    points += change
    cursor.execute("UPDATE users SET points = ? WHERE id=?",(points, id))
    connection.commit()
    return points

async def transferFromHouse(targetId:int, transferAmount:int):
    housePoints = await getPoints(houseId)
    if (housePoints<transferAmount):
        updatePoints(houseId, housePoints*-1)
    else:
        updatePoints(houseId, transferAmount*-1)
    updatePoints(targetId, transferAmount)

def transferPoints(sourceId:int, targetId:int, transferAmount:int):
    if (transferAmount<0):
        return "Error, transfer amount must be greater than or equal to zero"
    elif (getPoints(sourceId)<transferAmount):
        return "Error, you do not have anough points to transfer"
    else:
        updatePoints(sourceId, transferAmount*-1)
        updatePoints(targetId, transferAmount)
        return "? transfered "+transferAmount+" amount of points to ?"
        