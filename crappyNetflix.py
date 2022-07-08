import sqlite3
import getpass
import sys
from datetime import date
from search import *
def connect(path):
    # Function to connect to the database
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    cursor.execute(' PRAGMA foreign_keys=ON; ')
    connection.commit()
    return connection, cursor

#Make a login screen\
def login(connection, cursor):
    userID = input("Enter userID:")
    password = str(getpass.getpass(prompt="Enter new password"))
    password= str(password)
    queryC = "SELECT * FROM customers WHERE cid = ? AND pwd = ?"
    queryE = "SELECT * FROM editors WHERE eid = ? AND pwd = ?"
    cursor.execute(queryC,(userID,password,))
    if sqlite3.complete_statement(queryC,(userID,password,)):
        pass
    else:
        print("Incomplete query")
        print("You are logged out")
        return -1
    selectUser = cursor.fetchall()
    if selectUser:
        print(selectUser)
        return userID
    elif not selectUser:
        cursor.execute(queryE,(userID, password,))
        selectUser = cursor.fetchall()
        print(selectUser)
        if not selectUser:
            print("The user does not exist, do you want to signup? Please create a new user login")
            CustName = input("Enter new customer name")
            userID = input("Enter new userID")
            queryNewC = "SELECT cid FROM customers WHERE cid = ?"
            cursor.execute(queryNewC,(userID,))
            if sqlite3.complete_statement(queryNewC, (userID,)):
                pass
            else:
                print("Incomplete query")
                print("You are logged out")
                return -1
            checkUser = cursor.fetchall()
            userID = 0
            if checkUser:
                print("Please input a unique userID")
            password = str(getpass.getpass(prompt="Enter new password"))
            addNewCust = "INSERT INTO customers Values (?, ?, ?)"
            cursor.execute(addNewCust,(userID, CustName,password,))
    return userID

def main():
    path = "a3.db"
    connection, cursor = connect(path)
    userID = login(connection,cursor)
    print(userID)

    mySession = Session(connection, cursor,userID)
    if userID == 0:
        pass
        #go to the editor function else
    else:
        menu(userID,connection, cursor)

    connection.commit()
    connection.close()
    return
main()
