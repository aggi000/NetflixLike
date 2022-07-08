import sqlite3
import os
import getpass
import sys
import time
from datetime import date

class Search:

    def __init__(this, session):

        this.__cur = session.getCursor()
        this.__customerCode = session.getUserID()
        this.__conn = session.getConn()
        this.__session = session

    def __clearScreen(this):
        #Detect os
        if "linux" in sys.platform.lower():
            command = 'clear'
        elif "win" in sys.platform.lower():
            command = 'cls'
        os.system(command)

    def __process_words(this, search_entry):
        #Make the words lower case
        search_entry = search_entry.lower()


        #Display the result
        wordList = search_entry.split(",")

        #Strip any white spaces
        for i in range(len(wordList)):
            wordList[i] = wordList[i].strip()
        #Remove duplicate keywords
        wordList = set(wordList)
        wordList = list(wordList)

        return wordList

    def specific_search(this, search_entry):
        #Selects a non specific search

        wordList = this.__process_words(search_entry)

        MainQuery = """

        SELECT Universe.mid, Universe.title, Universe.year, Universe.runtime, Universe.mcount
        FROM  (SELECT DISTINCT m.mid AS mid, m.title AS title, m.year AS year, m.runtime AS runtime, {1} AS mcount
            FROM casts c, movies m, moviePeople mp
            WHERE c.mid = m.mid AND mp.pid = c.pid
            AND ({0})
            GROUP BY m.mid
            ORDER BY m.mid) as Universe

        ORDER BY Universe.mcount DESC"""


        #This where statement gets the matching keywords
        ExtraWhereStatement = """(LOWER(m.title) LIKE '%{0}%'
                   OR LOWER(mp.name) LIKE '%{0}%'
                   OR LOWER(c.role) LIKE '%{0}%')"""

        #Got part the counting substrings part from stack overflow, if any questions
        #email at jfernan1@ualberta.ca
        #https://stackoverflow.com/questions/738282/how-do-you-count-the-number-of-occurrences-of-a-certain-substring-in-a-sql-varch

        #We don't concatenate titles as there will only be one instance of a title, or any of it
        countTitleInstances =  """ ((LENGTH(LOWER(m.title)) - LENGTH(REPLACE(LOWER(m.title), '{0}', ''))) / LENGTH('{0}')) """

        countNameInstances = """((LENGTH(LOWER(GROUP_CONCAT(mp.name))) - LENGTH(REPLACE(LOWER(GROUP_CONCAT(mp.name)), '{0}', ''))) / LENGTH('{0}')) """

        countRoleInstances = """((LENGTH(LOWER(GROUP_CONCAT(c.role))) - LENGTH(REPLACE(LOWER(GROUP_CONCAT(c.role)), '{0}', ''))) / LENGTH('{0}')) """

        countTitleStatement = ''
        countNameStatement = ''
        countRoleStatement = ''


        fromStatement = ''
        whereStatement = ''
        joinStatement = ''
        totalStatement = ''
        for i in range(len(wordList)):
            keyWord = wordList[i].lower()
            #Parse the extra statement we need
            totalStatement += countTitleInstances.format(keyWord) + '+' + countNameInstances.format(keyWord) + '+' +countRoleInstances.format(keyWord) + '+'
            whereStatement += ExtraWhereStatement.format(keyWord) + " OR "

        whereStatement = whereStatement.rstrip(" OR ")
        totalStatement = totalStatement.rstrip('+')

        MainQuery = MainQuery.format(whereStatement, totalStatement)

        this.__cur.execute(MainQuery + ";")
        #For two we could ask for multiple keywords following a specific format and sort it out ourselves

        #We need to chec

        rows = this.__cur.fetchall()
        print("********************************Results*********************************")
        return rows

    def quit(this):
        pass
    def search_menu(this):
        entry = ''
        option = ''

        resultLimit = 5
        tableLength = 0
        while entry != 'exit' and option != 'exit':
            #Ask user to enter any amount of keywords
            print("*********************************Search Menu**************************************")
            option = ''
            entry = input("What would you like to search? ")
            entry = entry.lower()
            #If the user hasn
            if entry != '':
                rows = this.specific_search(entry)
                tableLength = len(rows)

            if tableLength <= 0:
                this.__clearScreen()
                print("No match was found please try again")
            else:
                currentLimit = resultLimit
                optionDic = this.__organize_movies(rows)
                this.__clearScreen()


            i = 0
            while entry != 'exit' and option.lower() != 'search' and option.lower() != 'exit' and tableLength > 0:

                #If i is less than the current limit then display rows
                if (i<currentLimit):
                    if (i < tableLength):
                        print("{0}. {1}" .format(i+1, optionDic[i+1][1:]))
                    i +=1
                #If i is greater or equal than the current limit then prompt the user to go forward or back
                elif (i >= currentLimit):
                    upperBoundary = currentLimit + (tableLength % resultLimit)


                    if currentLimit <= tableLength:
                        print("{0}/{1} results..." .format(currentLimit, len(rows)))
                    else:
                        print("{0}/{0} results..." .format(tableLength))

                    #Ask user whether they want to go forward or back

                    print("To go to the next page or back one page enter 'next' or 'back'")
                    print("To go back to the search menu enter 'search'")
                    print("To select a movie enter the movie number on the right like this eg. '1'")

                    option = input("What would you like to do?")
                    option = option.lower()
                    #If the user decides to go forward then go forward
                    if option == 'next':
                        this.__clearScreen()
                        #In this case this just implies add 5 more rows to display
                        if (upperBoundary <= tableLength):
                            currentLimit += resultLimit
                        else:
                            i = currentLimit - resultLimit
                    elif option == 'back':
                        this.__clearScreen()

                        #Subtract i in order to obtain  5 more results
                        if (i - resultLimit > 0):
                            #We want to go twice as back to print everything again
                            i -= resultLimit*2
                            currentLimit -= resultLimit
                        else:
                            i = 0
                            currentLimit = resultLimit

                    elif option.isnumeric() and int(option) in optionDic:

                        print("Took Option")
                        #Obtain the movie code
                        this.__clearScreen()
                        movieCode = optionDic[int(option)][0]

                        #Go into movie info
                        print(movieCode)
                        option = this.__movieInfoMenu(movieCode)


                        i = currentLimit - resultLimit
                    elif option =='exit':
                        entry = option
                    else:
                        #This is to print everything again within the loop
                        i = currentLimit - resultLimit
                        this.__clearScreen()

    def __movieInfoMenu(this, movieCode):
        #Get number of people who have watched this movie
        option = ''
        while option != 'back':
            watchCount = this.__getCustomerCount(movieCode)

            castMembers = this.__getCastMembers(movieCode)

            castMembers = this.__organize_movies(castMembers)
            print("*************************{0} People have watched this movie*********************************" .format(watchCount))
            print("++++++++++++++++++++++++++++++++Presented by++++++++++++++++++++++++++++++++")
            for i in range(len(castMembers)):
                print("{0}. {1} Playing as '{2}'".format(i+1, castMembers[i+1][1], castMembers[i+1][2]))


            print("If you want to follow a cast member type 'follow [CastNumber]'")
            print("If you want to watch the movie enter 'watch'")
            print("If you want to go back enter 'back'")

            option = input("What do you want to do? ")
            option = option.lower()
            if 'follow' in option:
                this.__clearScreen()
                castNumber = None
                followOption = option.split()
                if len(followOption) > 1:
                    castNumber = int(followOption[1])

                #Obtain cast member
                if castNumber in castMembers:
                    #Get cast code
                    castCode = castMembers[castNumber][0]
                    this.__followCastMember(castCode, this.__customerCode)
            elif 'watch' in option:
                movieOption = ''
                myMovie = Movie(this.__session, movieCode)
                myMovie.startWatchingMovie()

                this.__session.addMovie(myMovie)
                while movieOption != 'y':

                    movieOption = input("Do you want to finish watching the movie y/n? ")
                    movieOption = movieOption.lower()
                    if movieOption == 'y':
                        this.__clearScreen()
                        myMovie.finishWatchingMovie()
                    elif movieOption == 'exit':
                        this.__clearScreen()
                        return movieOption
            elif option == 'exit':
                return option
            else:
                this.__clearScreen()




    def __followCastMember(this, castCode, customerCode):
        InsertQuery = """INSERT INTO follows VALUES ('{0}','{1}')""" . format(customerCode, castCode)
        try:
            this.__cur.execute(InsertQuery)
            this.__conn.commit()
            print("--------------------Cast Member has been inserted succcesfully-----------------------")
        except:
            print("--------------------You already follow this cast member------------------------------")


    def __getCastMembers(this, movieCode):
        QUERY = """SELECT mp.pid, mp.name, c.role
        FROM casts c, moviePeople mp
        WHERE c.pid = mp.pid AND c.mid = '{0}'"""

        MainQuery = QUERY.format(movieCode)

        this.__cur.execute(MainQuery)
        result = this.__cur.fetchall()


        return result
    def __getCustomerCount(this, movieCode):

        QUERY = """SELECT COUNT(w.cid)
            FROM watch w
            WHERE w.mid = '{0}'
            GROUP BY w.mid
            """


        MainQuery = QUERY.format(movieCode)

        this.__cur.execute(MainQuery)

        result = this.__cur.fetchall()
        return result[0][0]
        #Get cast member of the movie

        #Allow user to either start watching it

        #Allow user to follow cast member

    def  __organize_movies(this, movieList):
        optionDic = {}

        for i in range(len(movieList)):
            optionDic[i+1] = movieList[i]

        return optionDic
    def __exit(this):
        this.__session.endSession()
class Session:
    def __init__(this, connection, cursor, userID):
        this.__userID = userID
        this.__connection = connection
        this.__cursor = cursor
        this.__sessionID = None
        this.__sdate = None
        this.__duration =None
        this.__movieList = []

    def startSession(this):
        queryNewSession = "INSERT INTO sessions Values (?, ?, ?, ?)"
        querySessionID = "SELECT sid FROM sessions ORDER by sid DESC"
        this.__cursor.execute(querySessionID)
        sessionIDList = this.__cursor.fetchall()
        print(sessionIDList[0][0])
        this.__sessionID = sessionIDList[0][0] + 1
        this.__sdate = date.today()
        #Get the starting time
        this.__duration = time.time()
        this.__cursor.execute(queryNewSession,(this.__sessionID, this.__userID, this.__sdate, 'NULL'))
        this.__connection.commit()
    def endSession(this):
        sessionEndQuery = """UPDATE sessions
                            SET duration = ?
                            WHERE sid = ?;"""
        #Get the total time in seconds
        this.__duration = time.time() - this.__duration
        #Get the total time in minutes
        this.__duration = this.__duration // 60

        #Finish watching all movies in the session
        if len(this.__movieList) >0:
            #If movie is still being watch then finish watching movie
            for movie in this.__movieList:
                if movie.isOpen():
                    movie.finishWatchingMovie();

        #End the session

        this.__cursor.execute(sessionEndQuery, (this.__duration, this.__sessionID))
        this.__connection.commit()
    def addMovie(this, movie):
        this.__movieList.append(movie)
    def getCursor(this):
        return this.__cursor
    def getConn(this):
        return this.__connection
    def getUserID(this):
        return this.__userID
    def getSessionID(this):
        return this.__sessionID
class Movie:

    def __init__(this, session, movieCode):
        this.__conn = session.getConn()
        this.__cursor = session.getCursor()
        #movie and session it belongs to
        this.__movieID = movieCode
        this.__userID = session.getUserID()
        this.__sessionID = session.getSessionID()
        this.__duration = None
        this.__currentlyWatching = False
    def startWatchingMovie(this):

        #Insert query
        movieStartQuery = """INSERT INTO watch VALUES ('{0}', '{1}', '{2}', {3})""".format(this.__sessionID, this.__userID, this.__movieID, 'NULL')
        this.__duration = time.time()
        this.__currentlyWatching = True
        this.__cursor.execute(movieStartQuery)
        this.__conn.commit()


    def finishWatchingMovie(this):
        #This makes sure that if the movie duration is greater than the movie
        #The duration of the watch time gets set to just the runtime of the movie


        #I know I could technically create a trigger for this, but I do not know
        #how to do it and it hasn't been discussed in class how to compare 2 tables in a trigger
        #Therefore I will compare it in code, but beware that I am aware that a
        #trigger could technically be created for this

        #I could also have technically created a trigger for each
        #Insert but that would have taken way too much space, therefore I consider
        #This to be the optimal solution within my given means in this assignment -Juan Fernandez

        this.__duration = (time.time() - this.__duration) // 60
        runtime = this.__getRunTime()

        if this.__duration > runtime:
            this.__duration = runtime

        movieEndQuery = """UPDATE watch
                            SET duration = {0}
                            WHERE sid = '{1}' AND cid = '{2}' AND mid = '{3}';""".format(this.__duration, this.__sessionID, this.__userID, this.__movieID)
        print(movieEndQuery)

        movieStatement = movieEndQuery
        this.__cursor.execute(movieStatement)
        this.__conn.commit()
        this.__currentlyWatching = False
    def __getRunTime(this):

        runtimeQuery = """SELECT m.runtime
        FROM movies m
        WHERE m.mid = {0};""" .format(this.__movieID)
        this.__cursor.execute(runtimeQuery)

        rows = this.__cursor.fetchall()

        runtime = int(rows[0][0])
        return runtime
    def isOpen(this):
        return this.__currentlyWatching
#For editor function

#The editor should be able to select a monthly, annual, or all time report

#Select all movie pairs watch by a customer within the last 30 days

#Select all movie pairs watched by a customer within the last year

#Sellect all movie pairs watched by customers from all time
"""SELECT COUNT(w1.cid) ,m1.mid,m1.title, m2.mid,m2.title
FROM movies m1, movies m2, watch w1, watch w2, sessions s
WHERE w1.mid = m1.mid AND w2.mid = m2.mid
AND m1.mid != m2.mid
AND w1.cid = w2.cid
AND s.sdate between date ('now','-365 days') and date('now')
GROUP by m1.mid, m2.mid
ORDER by Count(w1.cid) DESC;"""
