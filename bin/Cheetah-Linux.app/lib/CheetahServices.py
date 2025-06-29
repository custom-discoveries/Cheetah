#**************************************************************************************
# Copyright (c) 2024, Custom Discoveries Inc.
# All rights reserved.
# CheetahServices.py - This module provides all the services to the Cheetah application
#**************************************************************************************

from os.path import exists
import os
import re
import sys
import csv
import json
import time
import datetime
import calendar
import traceback
import shutil
from prompt_toolkit import prompt
from datetime import date
from datetime import datetime
from typing import Dict, Union, Set, List
from pathlib import Path
import requests
import subprocess
import pyTigerGraph as tg

from pyTigerGraph import TigerGraphConnection
from CheetahConfigure  import CheetahConfigure
#
# Setup Virtual Environment
# Terminal Window$ python3 -m venv .venv

class CheetahServices:

    QUERIES="Queries"
    SCHEMA="Schema"
    DATA="Data"
    ALL_FILES = "ALL"

    foundAlias = False
    cachedQueries = {}
    MonthInSeconds = 2592000

    def __init__(self, username="", password="", projectDir="", graphname="", host="", version = "", 
                 remoteServer="", configObj:Union[CheetahConfigure, None] = None): 
        if (configObj != None):
            self.configure = configObj
            self.userName = None
            self._passWord = None
            self.graphName = None
            self.host:Union[str,None] = self.configure.getHost()
            self.version:Union[str,None] = self.configure.getVersion()
            self._secret = ""
            self._adminSecret = ""
            self._token = None
            self._conn = None
            self.tgCloud = False
            self._tokenExpirationDate = None
            self.serverOnLine = False
        else:
            self.userName = username
            self._passWord = password
            self.graphName = graphname
            self.host = host
            self.version = version
            self._secret = ""
            self._adminSecret = ""
            self._token = None
            self._conn = None
            self.tgCloud = False
            self.localRemote = False
            self._tokenExpirationDate = None
            self.serverOnLine = False
            self.configure = CheetahConfigure()
            self.configure.setRemoteServer(remoteServer)
            self.configure.setVersion(version)
            self.configure.setProjectDir(projectDir)
            self.configure.setHost(host)
            self.configure.setGraphName(graphname)
        
        self.systemServices = SystemUtilities(self)
        self.systemSecrets = SystemSecrets(self)
        self.systemQueries = SystemQuery(self)
    #
    # Initialize Connection by reading configuration file
    #
    def initConnection(self):

        try:
            if (self._conn == None or (self._secret == None or self._secret == "")):
                self.configure.retrieveTGAdminConf()
                self.graphName = self.configure.getGraphName()
                self.userName = self.configure.getUserName()
                self._passWord = self.configure.getPassWord()

                if self.configure.getRemoteServer() == True:
                    self.host = self.configure.getHost()
                    if self.host.find("tgcloud.io") > 0:
                        self.tgCloud = True
                        self.localRemote = False
                    else:
                        self.tgCloud = False
                        self.localRemote = True

                    #self.userName = self.configure.getUserName()
                    self._adminSecret = self.configure.getAdminSecret()

                    if self.userName == None:
                        self.userName = "__GSQL__secret"
                        self._passWord = self._adminSecret
                    #else:
                    #    if(self._passWord == None):
                    #        self._passWord = self.configure.getPassWord()

                    #self._secret = self.configure.getSecret()
                else:
                    self.host = 'http://localhost'
                    self.configure.setHost(self.host)
                    self.tgCloud = False
                    self.localRemote = False

                self.version = self.configure.getVersion()
                self._secret = self.configure.getSecret()
                self._token = self.configure.getToken()


                #
                # July 2022 new release of TigerGraph Cloud, revamped the secrurity
                # login model from pyTigerGraph API.  No need to pass in username or password
                # login is now done with a secret.  So, you need to go to tgcloud and crate a secrect
                # and pass it as either a gsqlSecret parameter or pass username (__GSQL__secret) and
                # secrect as password
                #
                self._conn = tg.TigerGraphConnection(host = self.host,
                                                graphname = self.graphName,
                                                username = self.userName,
                                                password = self._passWord,
                                                apiToken = self._token,
                                                gsqlVersion = self.version,
                                                tgCloud = self.tgCloud)
                #if len(self._adminSecret) == 0:
                    #self.createSecret(self.graphName)
                    #elif self.foundAlias == False:
                    #self.displaySecrets(False)
                
                self._tokenExpirationDate = self.configure.getTokenExpirationDate()
            else:
                return self._conn
        except IndexError as error:
            print("initConnection() Error: No Graph Exists:",self.graphName)
            raise PermissionError("No Graph Exists {self.graphName } Please create a Schema")
        except Exception as error:
            #print("initConnection Error:",repr(error))
            if error.args[0].find("exists.") >0 :
                #self._conn.gsql("DROP GRAPH "+ self.graphName)
                print("Your Config File is out of Sync with your Secrets for Graph:", self.graphName,"\nPlease login to your database a delete your secrets under Admin Portal -> Management -> Users")
                raise LookupError("\nYour Config File is out of Sync with your Secrets for Graph {self.graphName}")

        return self._conn

    def getConnection(self) -> TigerGraphConnection:
            return self._conn

    def isICloud(self, version):
        try:
            if version == None:
                versionNumber = self.extractVersionNumber()
                if versionNumber != None:
                    self.configure.setVersion(versionNumber)
                    version = versionNumber
                    zzVersion = version.split('.')
                    return zzVersion[0]>="4" and zzVersion[1]>"0"                        
            else:
                zzVersion = version.split('.')
                return zzVersion[0]>="4" and zzVersion[1]>"0"
        except Exception as error:
            print(f"Could not extract version number...")
            return False

    def deleteToken(self):
        if (self.configure.getToken() != ''):
            url=f"{self.configure.getHost()}:9000/requesttoken"
            data = {}
            data["secret"] = self.configure.getSecret()
            data["token"] = self.configure.getToken()

            results = requests.delete(url,data=json.dumps(data),verify=False)

            if results.reason == 'OK':
                token = ''
                self.configure.setToken(token)
                self.configure.writeTGAdminConf()

            print("Deleted Token =",results.status_code)

    def createGraph(self) -> bool:
        self.initConnection()

        rs = self.getConnection().gsql(f"CREATE GRAPH {self.graphName}()")
        print(rs)
        if rs.find("created") >=0 and self.configure.getRemoteServer() == True:  # type: ignore
            self._secret = ''
            self._token = ''
            #self.createSecret(self.configure.getSecretAlias())
        else:
            return False

        return True

    def deleteGraph(self) -> bool:
        self.initConnection()
        try:
            rs = self.getConnection().gsql("DROP GRAPH {self.graphName}")

            print(rs)
            if rs.find("dropped") >=0 and self.configure.getRemoteServer() == True:  # type: ignore
                return True
            else:
                return False
        except Exception as e:
            print("ERROR - Delete Grape:",e)
            return False


    def deleteJobs(self) -> bool:
        self.initConnection()
        try:
            rs = self.getConnection().gsql("DROP JOB ALL ")

            print(rs)
            if rs.find("dropped") >=0 and self.configure.getRemoteServer() == True: # type: ignore
                return True
            else:
                return False
        except Exception as e:
            print("ERROR - Delete Grape:",e)
            return False

    def deleteJobsAndGraph(self) -> bool:
        self.initConnection()
        try:
            print("Deleting ALL Jobs...")
            rs = self.getConnection().gsql("DROP JOB ALL ")

            print("Deleting Graph...",self.graphName)
            rs = self.getConnection().gsql("DROP GRAPH {self.graphName}")

            print(rs)
            if rs.find("dropped") >=0 and self.configure.getRemoteServer() == True:  # type: ignore
                return True
            else:
                return False
        except Exception as e:
            print("ERROR - Delete Grape:",e)
            return False

    def stopWatch(self,startTime=None,formattedTime=False) -> Union[datetime, str]:

        if startTime == None:
            return datetime.now()
        else:
            stopTime = datetime.now()
            totalTime = stopTime - startTime
            displayTime,displayLabel = self.formattedDisplyTime(totalTime)
            if formattedTime == True:
                ##print("StopTime = ",stopTime)
                ##return f"Total Time = {displayTime:.2f} {displayLabel}"
                return displayTime, displayLabel
            else:
                return totalTime

    def formattedDisplyTime(self, totalTime):
       if (totalTime.total_seconds() >= 3600):
           displayTime = f"{totalTime.total_seconds()/3600:.2f}"
           displayLabel = "Hours"
       if (totalTime.total_seconds() >= 60):
          displayTime = f"{totalTime.total_seconds()/60:.2f}"
          displayLabel = "Minutes"
       else:
          displayTime = totalTime.total_seconds()
          displayLabel = "Seconds"
       return displayTime,displayLabel

    def isServerRunning(self) -> bool:
        restppStatus = None
        try:
            #self.initConnection() 
            if self._conn != None:            
                restppStatus = self.getConnection().ping()
            #restppStatus = self.getConnection().echo()
            #restppStatus = self.getConnection()._get(self.getConnection().restppUrl + "/echo/", resKey="message")
            #restppStatus = subprocess.check_output('curl -X GET "https://df01b07619ce45a2a88f6481bbb25e55.i.tgcloud.io:443/restpp/echo"',shell=True)
            #restppStatus = restppStatus.decode()
            if restppStatus != None and not restppStatus.get("error"):
                self.serverOnLine = True
            else:
                self.serverOnLine = False

        except Exception:
                #print("Error in isServerRunning",repr(error))
                #traceback.print_exc()
                self.serverOnLine = False

        return self.serverOnLine

    def setAdminRestfulEndpoints(self):

        if self.configure.getRemoteServer() == False:
            restppStatus = subprocess.check_output('gadmin config get RESTPP.Factory.EnableAuth',shell=True)
            restppStatus = restppStatus.decode()
            restppStatus = restppStatus in ["true"]
            #print("RESTPP.Factory Decoded =",restppStatus)

            if restppStatus == False:
                subprocess.run('gadmin config set RESTPP.Factory.EnableAuth true',shell=True)
                subprocess.run('gadmin config apply',shell=True)


    def processSchemas(self,schemaName=None):
        process_intake = True
        quitSet = ('','q','Q','quit','Quit','QUIT','end')
        try:
            while (process_intake == True) :

                errorFlag = True
                self.initConnection()
                schemaDir = self.configure.getDDLSchemaDir()

                if schemaName == None:
                    listDir = self._listDDLFiles(schemaDir)
                    if len(listDir) > 1 :
                        print('(0) To Install All Above Schemas...')
                        print('(q) To quit...')

                    while errorFlag == True:
                        index = input("Please select Schema Option: ")
                        listIndex = index.split(',')
                        for index in listIndex:
                            if len(index) > 0 and index.isnumeric() == True:
                                errorFlag = False
                            elif (index.isnumeric() == False and index in quitSet ):
                                errorFlag = False
                                break
                            elif (index.isnumeric() == False) :
                                errorFlag = True
                                break

                    if index in quitSet :
                        process_intake = False
                        return

                    for index in listIndex:
                        index = int(index)
                        if index > 0 and index <= (len(listDir)):
                            fullSchemaName = listDir[index-1]
                            fullSchemaName = fullSchemaName+".gsql"
                            print("Installing Schema File:",fullSchemaName)
                            schemaFile = self.configure.getDDLSchemaDir()/Path(fullSchemaName)
                            self.installSchema(schemaFile)

                        elif index == 0:
                            schemaName = self.ALL_FILES

                    if len(listDir) == 1:
                        process_intake = False

                if schemaName == self.ALL_FILES:
                    process_intake = False
                    listDir = self._listDDLFiles(schemaDir,displayFiles=False)

                    for query in listDir:
                        fullSchemaName = query+".gsql"
                        schemaFile = self.configure.getDDLSchemaDir()/Path(fullSchemaName)
                        self.installSchema(schemaFile)

                elif schemaName != None:
                    schemaFile = schemaName+".gsql"
                    schemaFile = self.configure.getDDLSchemaDir()/Path(schemaFile)

                    print("Installing Schema",schemaName)
                    self.installSchema(schemaFile)

        except Exception as error:
            print("processSchemas() Error:",error)
            return error

    def installSchema(self,schemaFile:Path) -> bool:

        self.cachedQueries = {}
        lineCount = 0
        processing_global_variables = False
        loadString = ""
        _dataFileDictonary = ""

        if self.configure.getRemoteServer() == False:

            print(f"Installing on Local Server Schema File: {schemaFile}")
            results = subprocess.run(f"gsql -u {self.userName} -p {self._passWord} '{schemaFile}' ", shell=True)
            #print(f"Resuts from subprocess = {results.returncode}")
            if results.returncode == 0:
<<<<<<< HEAD
                self.installSecrets(processing_global_variables)            
            #input("\nPress Enter to continue: ")
=======
                self.systemSecrets.installSecrets(processing_global_variables)            
            input("\nPress Enter to continue: ")
>>>>>>> iCloud4.1.2
        else:
            try:
                _dataFileDictonary = self._extractSchemaLoad(schemaFile)
                localGraphName = _dataFileDictonary.get("graphName")
                if len(localGraphName) == 0:
                    processing_global_variables = False
                elif localGraphName != self.configure.getGraphName():
                    raise PermissionError("Graph Name " + localGraphName + " defined in Schema DDL does not match Graph Name in remoteAdminConfig.txt file " + self.configure.getGraphName() + " Please check case sensitivity or DDL Statement...")

                inFile = open(schemaFile)

                for line in inFile:
                    loadString = loadString + line
                    lineCount +=1

                conn = self.initConnection()
                results = conn.gsql(loadString)
                print(results)
                #
                # Determine if we dropped the schema
                # by displaying the secrets, if not found
                # Catch exception and create new Secret/Token
                #
                if (results.find("Successfully created") > 0):
<<<<<<< HEAD
                    self.installSecrets(processing_global_variables)
=======
                    self.systemSecrets.installSecrets(processing_global_variables)
>>>>>>> iCloud4.1.2
                else:
                    raise LookupError("Failed to create schema change jobs")

            except Exception as error:
                print("installSchema() Error:",error)
                return False

            return True
<<<<<<< HEAD

    def installSecrets(self, processing_global_variables):
        results = self.hasExistingSecrets()
        if results == False and processing_global_variables == False:
            rs = self.createSecret(self.configure.getSecretAlias())
            if (rs == True):
                print("\n******* Warning *******")
                print("Make sure to store the Secret & Token values in a safe plase, Once you hit enter, you will not be able to retrieve these values")
                            #
                            # Now that we have a token, update the version number
                            #
                if (self.configure.getVersion() == None):
                    versionNumber = self.extractVersionNumber()
                    self.configure.setVersion(versionNumber)
                    self.configure.writeTGAdminConf()
            #print("Number of Lines in File =", lineCount)
            #print(loadString)
=======
>>>>>>> iCloud4.1.2

    def loadData(self,dataName=None):
        process_intake = True
        quitSet = ('','q','Q','quit','Quit','QUIT','end')
        while (process_intake == True) :
            try:
                errorFlag = True
                dataDir = self.configure.getDDLDataDir()

                if dataName == None:
                    listDir = self._listDDLFiles(dataDir)
                    print('(0) To Install All Above Data DLL Files...')
                    print('(q) To quit...')

                    while errorFlag == True:
                        index = input("Please select Data File Option: ")
                        listIndex = index.split(',')
                        for index in listIndex:
                            if len(index) > 0 and index.isnumeric() == True:
                                errorFlag = False
                            elif (index.isnumeric() == False and index in quitSet ):
                                errorFlag = False
                                break
                            elif (index.isnumeric() == False):
                                errorFlag = True
                                break

                        if (index in quitSet):
                            process_intake = False
                            return

                    for index in listIndex:
                        index = int(index)
                        if index > 0 and index <= (len(listDir)):
                            fullDataName = listDir[index-1]
                            fullDataName = fullDataName+".gsql"
                            print("Installing Data File:",fullDataName)
                            dataFileName = self.configure.getDDLDataDir() / Path(fullDataName)
                            self.createDataJobs(dataFileName)

                        elif index == 0:
                            dataName = self.ALL_FILES

                if dataName == self.ALL_FILES:
                    listDir = self._listDDLFiles(dataDir,displayFiles=False)

                    for query in listDir:
                        fullDataName = query+".gsql"
                        dataFileName = self.configure.getDDLDataDir() / Path(fullDataName)
                        self.createDataJobs(dataFileName)

                    process_intake = False
                elif dataName != None:
                    dataFileExt = dataName+".gsql"
                    dataFileName = self.configure.getDDLDataDir() / Path(dataFileExt)
                    print("Installing Data File:",dataName)
                    self.createDataJobs(dataFileName)

            except LookupError as error:
                return False

            except Exception as error:
                print("installData() Error:",error)
                #return error
            return True


    def processUDF_Functions(self, get=False):

        try:
            conn = self.initConnection()
            if self.configure.getRemoteServer() == False:
                if get==True:
                    print("Saving ExprUtil TO ./Outputs/ExprUtil.hpp")
                    subprocess.run(f"gsql -u {self.userName} -p {self._passWord} 'GET ExprUtil TO \"./Outputs/ExprUtil.hpp\"'",shell=True)
                    print("Saving ExprFunctions TO ./Outputs/ExprFunctions.hpp")
                    subprocess.run(f"gsql -u {self.userName} -p {self._passWord} 'GET ExprFunctions TO \"./Outputs/ExprFunctions.hpp\"'",shell=True)
                else:
                    subprocess.run("gadmin config set GSQL.UDF.Policy.Enable false",shell=True)
                    subprocess.run("gadmin config set GSQL.UDF.EnablePutExpr true",shell=True)
                    subprocess.run('gadmin config apply',shell=True)
                    print("Reading ExprUtil FROM ./UDF/ExprUtil.hpp")
                    subprocess.run(f"gsql -u {self.userName} -p {self._passWord} 'PUT ExprUtil FROM \"./UDF/ExprUtil.hpp\"'",shell=True)
                    print("Reading ExprFunctions FROM ./UDF/ExprFunctions.hpp")
                    subprocess.run(f"gsql -u {self.userName} -p {self._passWord} 'PUT ExprFunctions FROM \"./UDF/ExprFunctions.hpp\"'",shell=True)
                    subprocess.run("gadmin config set GSQL.UDF.Policy.Enable true",shell=True)
                    subprocess.run("gadmin config set GSQL.UDF.EnablePutExpr false",shell=True)
                    subprocess.run('gadmin config apply',shell=True)
            else:
                if get==True:
                    udfStatement = "ExprFunctions.hpp"
                    self.getUDF(udfStatement)

                    udfStatement = "ExprUtil.hpp"
                    self.getUDF(udfStatement)
  
                else:
                    udfStatement = self.configure.getProjectDir()+"UDF/ExprFunctions.hpp"
                    if exists(udfStatement):
                        conn.installUDF(ExprFunctions=udfStatement)
                    else:
                        raise NameError("processUDF_ExprFunctions() Error: File Not Found: ", udfStatement)

                    udfStatement = self.configure.getProjectDir()+"UDF/ExprUtil.hpp"
                    if exists(udfStatement):
                        conn.installUDF(ExprUtil=udfStatement)
                    else:
                        raise NameError("processUDF_ExprUtil() Error: File Not Found: ", udfStatement)

        except Exception as error:
                    print("processUDF_Functions() Error:",repr(error))

    def getUDF(self,udfFileName):
        try:
            conn = self.getConnection()
            results = []

            if (udfFileName == "ExprFunctions.hpp"):
                print(f"Saving {udfFileName} TO ./Outputs/{udfFileName}")
                results = conn.getUDF(ExprFunctions=True,ExprUtil=False)
                outFile = open(self.configure.getProjectDir() + f"Outputs/{udfFileName}",'w')
                outFile.write(results)
            elif (udfFileName == "ExprUtil.hpp"):
                print(f"Saving {udfFileName} TO ./Outputs/{udfFileName}")
                results = conn.getUDF(ExprFunctions=False,ExprUtil=True)
                outFile = open(self.configure.getProjectDir() + f"Outputs/{udfFileName}",'w')
                outFile.write(results)

        except Exception as error:
                print("getUDF() Error:",repr(error))


    def createDataJobs(self,dataFileName):

        jobID = None
        files = None
        fileName = None
        splitFlag = False
        seperationStr = ","
        index = -1
        max_retries = 3

        try:

            if self.configure.getRemoteServer() == False:
                #print(f"createDataJob - Secret = {self._secret}")
                results = subprocess.run(f"gsql -u {self.userName} -p {self._passWord} '{dataFileName}' ", shell=True)
                #print(f"createDataJob - run command: {results}")

            else:
                conn = self.getConnection()

                _dataLoadCommands = self._extractDataJob(dataFileName)
                localGraphName = _dataLoadCommands.get("graphName")

                if localGraphName != self.configure.getGraphName():
                    raise PermissionError("Graph Name defined in Load Data DDL does not match Graph Name in config file. Please check case sensitivity")

                #
                # Create the Load Job
                #
                results = conn.gsql(_dataLoadCommands.get("jobString"))
                print(results)
                index = results.find("Success")
                if index >=0:
                    loadJobs = _dataLoadCommands.get("jobs")

                    for job in loadJobs:
                        jobList = loadJobs.get(job)
                        for item in jobList:
                            if item[0] == "FILENAME":
                                jobID = job
                                dataSource = item[1]
                                fileName = item[2]
                                if len(item) == 4:
                                    seperationStr = item[3]

                                filesList = self._splitLargeFiles([[dataSource, fileName]])
                                if len(filesList) > 1:
                                    splitFlag = True

                                print(jobID, dataSource,dataFileName)

                                for file in filesList:
                                    retries = 0
                                    while retries < max_retries:
                                        try:
                                            fileName = self.configure.getGraphDataDir() / file[1]
                                            dataSource = file[0]
                                            self.processUpLoad(fileName, jobID, file, dataSource, seperationStr)
                                            retries = max_retries
                                        except Exception as e:
                                            retries += 1
                                            print(f"Attempt {retries} failed with exception: {e}")
                                            if retries < max_retries:
                                                print(f"Retrying... (attempt {retries + 1})")
                                                time.sleep(5)
                                            else:
                                                print("Max retries reached. Giving up.")
                                                self.clearSplitFiles(splitFlag)
                                                raise
                            #
                            # Clean up and delete Data Load Job
                            #
                            elif item[0].lower() == "drop":
                                if item[1].lower().find("job") >=0:
                                    results = self.getConnection().gsql(f"USE GRAPH {conn.graphname} {item[1]}")
                                    print(results)
                                elif item[1].lower().find("graph") >=0:
                                    results = self.getConnection().gsql(item[1])
                                    print(results)
                else:
                    if (self._token == ''):
                        raise LookupError("Missing Token" + self._token)

        except Exception as error:
            print("createDataJobs() Error:",repr(error))
            #print(traceback.format_exc())
            raise LookupError(error)

        self.clearSplitFiles(splitFlag)

    def clearSplitFiles(self, splitFlag):
        if splitFlag == True:
            dir_list = self.configure.getGraphDataDir().glob('tgAdmin_*')
            for dir_path in dir_list:
                #print(f"Deleting Dir: {dir_path}")
                shutil.rmtree(dir_path)


    def processUpLoad(self, fileName, jobID, file, dataSource, seperationStr):
        try:
            startTime = self.stopWatch()
            print(f"{startTime} Uploading Job Name={jobID} DS={dataSource} File={file[1]}")
            #
            # Default File Limit to 128MB, & 200 timeout seconds
            #
            results = self.getConnection().runLoadingJobWithFile(filePath=fileName, fileTag=dataSource, jobName=jobID, sep=seperationStr, timeout=200000)
            displayTime, displayLabel = self.stopWatch(startTime,formattedTime=True)
           
            print(f"Total Time = {displayTime:.2f} {displayLabel}")
            print(f"{json.dumps(results, indent=4, separators=('. ', ' = '))}")
            #
            # Give server sometime to process files...
            #
            time.sleep(2)

        except Exception as error:
            print("processUpLoad() Error:",repr(error))
            # print(traceback.format_exc())
            raise error

    def clearData(self):

        try:
            conn = self.initConnection()
            queryStatement = "clear graph store -HARD"
            answer = input("Cleansing ALL the data from " + self.configure.getGraphName()+" Are you sure(Y/N)?:")
            if answer in ['y', 'Y', 'Yes', 'yes', 'Ok', 'ok', 'gtg']:
                results = conn.gsql(queryStatement, self.configure.getGraphName())
                print(results)
        except Exception as error:
            print("clearData() Error:",error)

    def exportData(self):

        ymd = date.today()
        dumpDir = self.configure.getProjectDir() + 'Dump-' + str(ymd)
        os.makedirs(dumpDir,exist_ok=True)
        try:

            conn = self.initConnection()
            queryStatement = 'export GRAPH ALL TO \"''' + dumpDir +'\"'
            results = conn.gsql(queryStatement, self.configure.getGraphName())
            print(results)
        except Exception as error:
            print("exportData() Error:",error)


    #
    # Display the Database License Info for Remote run server
    #
    def displayLicense(self):
        #results = self.getConnection().getLicenseInfo()
        results = subprocess.run('gadmin license status',shell=True)
        print(results)
    
    def loadLicense(self,fileName:str):
        try:
            if self.configure.getRemoteServer() == False:
                if (fileName == "" ):
                    self.displayLicense()
                else:
                    subprocess.run(f"gadmin license set @{Path(fileName)}", shell=True)
                    #print(results.returncode)
                    subprocess.run('gadmin config apply', shell=True)
                    #print(results.returncode)
        except Exception as err:
            print(f"Error on loadLicense Call.. {err}")
            return False
        
        return True
    #
    # Extract Version Number to put in Configuration File
    #
    def extractVersionNumber(self):
        try:
            if self.configure.getRemoteServer() == False:
                completedProcess = subprocess.run('gadmin version',shell=True, capture_output=True)
                versionString = completedProcess.stdout.decode()
                index = versionString.find("\n")
                versionNumber = versionString[index-5:25]
                return (versionNumber)
            else:
                results = self.getConnection().getVersion()
                if (len(results) > 0):
                    versionString = results[0]['version']
                    versionNumber = (versionString.split("_"))[1]
                    return (versionNumber)

        except Exception as err:
             print(f"Error on Get Version Call.. {err}")
             print("Please create a Secret/Token to view database Version...")
             raise Exception(err)


    def showInstalledTags(self):

        foundTags = False
        listOfTags = []

        conn = self.initConnection()
        results = conn.gsql("USE GRAPH "+conn.graphname+" ls")
        results = results.splitlines()

        for line in results:
            if foundTags == True:
                index = line.find("- ")
                if (index > -1):
                    listOfTags.append(line[index+2:len(line)])

            index = line.find("Tags:")
            if (index == 0):
                foundTags = True

        count = 0
        for tag in listOfTags:
            if len(tag) > 0:
                count = count + 1
                print("(" + str(count) + ")",tag)

        return listOfTags
    
    def _extractDataJob(self,loadFile) -> Dict:

        lineCount = 0
        jobName = ""
        jobString = ""
        localGraphName = ""
        seperationStr = ","
        EOJFlag = False
        _dataJobDictonary = {}
        _dataFileDictonary = {}

        try:
            inFile = open(loadFile)
            for line in inFile:
                if (not line.find("#") >=0 and line.lower().find("create") >=0) and (line.lower().find("job") >=0):
                    EOJFlag = False
                    commandLine = line.split()
                    jobName = commandLine[3]
                    localGraphName = commandLine[6]
                    _dataJobDictonary.update({jobName:[]})

                if line.find("}") >=0:
                    EOJFlag = True
                    jobString = jobString + line

                elif not line.find("#") >=0 and (line.lower()).find("define filename") >=0:
                    # Extract DataSource and Filename from data load file
                    dataSource = self._extractDataSource(line)
                    dataFiles = _dataJobDictonary.get(jobName)
                    dataFiles.append([dataSource[1], dataSource[2], dataSource[4]])

                    # Define only Data Source minus the file name
                    # Data Files will be loaded as part of Run Job
                    jobString = jobString + dataSource[0] + " " + dataSource[1] + " " + dataSource[2] + ";\n"
                
                elif not line.find("#") >=0 and (line.lower()).find("load ") >=0:
                    self._extractSeparator(line, dataFiles)
                    jobString = jobString + line
                elif not line.find("#") >= 0 and (line.lower()).find("run ") >=0:
                    jobDir = _dataJobDictonary.get(jobName)
                    jobDir.append(["RUN",line])
                elif EOJFlag == True and line.find("#") < 0 and (line.lower()).find("drop") >=0:
                    jobDir = _dataJobDictonary.get(jobName)
                    jobDir.append(["DROP",line])
                    #EOJFlag = False
                else:
                    jobString = jobString + line

                lineCount +=1
        except Exception as error:
            print("_extractDataJob() Error:",error)
            #traceback.print_exc()

        _dataFileDictonary.update({"graphName" :localGraphName})
        _dataFileDictonary.update({"jobs" : _dataJobDictonary})
        _dataFileDictonary.update({"jobString" :jobString})
        _dataFileDictonary.update({"dataSource" :dataFiles})
        return  _dataFileDictonary

    def _extractSeparator(self, line, dataFiles):
        loadDataElements = line.split()
        for fileSource in dataFiles:
            if fileSource[1] == loadDataElements[1]:
                index = line.find("separator=")
                if index > -1:
                    fileSource.append(line[index+11])
                break
        
    def _extractDataSource(self,line):

        dataElements = line.split()
        fileParts = dataElements[4]
        index = fileParts.find('"')
        aFilePart = fileParts[index+2:(len(fileParts)-2)]
        aFile = os.path.basename(aFilePart)
        dataElements[4] = aFile

        return dataElements

    def _splitLargeFiles(self, dataFiles):
        newFiles = []
        try:
            for fileSource in dataFiles:
                file = Path(fileSource[1])
                ext = file.suffix
                #index = file.as_posix().find(".csv")
                #fileWOExt = file.as_posix()[:index]
                fileWOExt = file.stem

                fileName = self.configure.getGraphDataDir() / file
                filePath = self.configure.getGraphDataDir() / Path('tgAdmin_'+fileWOExt)
                file_size = os.stat(fileName).st_size
                #
                # If File Size is over splitMaxFileSize (default setting of 100MB), then split it
                # into SplitMaxLines (default setting of 100,000 lines) per file
                #
                maxFileSize = int(self.configure.getSplitMaxFileSize())
                numberOfLines = int(self.configure.getSplitMaxLines())

                if file_size > maxFileSize:
                    formatted_value = format(maxFileSize, ',')
    
                    if not (exists(self.configure.getGraphDataDir() / Path("tgAdmin_"+fileWOExt))):
                        print(f">>> NOTICE: Data file larger than splitMaxFileSize: {formatted_value} Bytes.")
                        os.mkdir(self.configure.getGraphDataDir() / Path("tgAdmin_"+fileWOExt))
                        #print(f"split -a 3 -dl {numberOfLines} \"{self.configure.getGraphDataDir() / file}\" \"{self.configure.getGraphDataDir()/Path('tgAdmin_'+fileWOExt+'/'+fileWOExt)}\", shell=True")
                        print(f">>> Please Standby.. Splitting File {file} with {numberOfLines} lines per file...")
                        print(f"to directory: {filePath} ")
                        subprocess.run(f"split -a 3 -dl {numberOfLines}  \"{self.configure.getGraphDataDir()/file}\" \"{self.configure.getGraphDataDir()/Path('tgAdmin_'+fileWOExt+'/'+fileWOExt)}\" ", shell=True)
                    
                    zzFiles = os.listdir(self.configure.getGraphDataDir()/Path("tgAdmin_"+fileWOExt))
                    print(">>> NOTICE: Number of Files Created are:",len(zzFiles))
                    for num in range(len(zzFiles)):
                        if num < 10:
                            newFiles.append([fileSource[0], "tgAdmin_"+fileWOExt+"/"+fileWOExt+'00'+str(num)])
                        elif (num >= 10 and num < 100):
                                newFiles.append([fileSource[0], "tgAdmin_"+fileWOExt+"/"+fileWOExt+'0'+str(num)])
                        elif (num >= 100):
                                newFiles.append([fileSource[0], "tgAdmin_"+fileWOExt+"/"+fileWOExt+str(num)])

                        #print( fileSource[0], "tgAdmin_"+fileWOExt+"/"+fileWOExt+'0'+str(num))
                else:
                    newFiles.append([fileSource[0], file])
        except FileExistsError as error:
            print("_splitLargeFiles() Error:",repr(error))
            self.clearSplitFiles(splitFlag=True)
            raise FileExistsError("Please try running Data Jobs Again...")

        return newFiles

    def _sortByNum(self,x):
        d={int:0, float:0, str:1}

        i1 = x.find("[")+1
        i2 = x.find("]")
        if x[i1:i2].isdigit():
            x = int(x[i1:i2])
        return d.get(type(x), 0), x

    def _listDDLFiles(self,ddlFullPath:Path,displayFiles=True):

        ddlDir = ddlFullPath
        resultsDir = []

        if ddlDir != None:
        #
        # Build a list of DDL only files (that end in .gsql), but without the extention
        #
            count=1
            filelist = os.listdir(ddlDir)
            filelist.sort(key=self._sortByNum)
            print("\n")
            for ddlFile in filelist:
                if ddlFile.endswith(".gsql"):
                    index = ddlFile.find(".gsql")
                    resultsDir.append(ddlFile[:index])
                    if displayFiles == True:
                        print('('+str(count)+')',ddlFile[:index])
                        count += 1

        return resultsDir


    def _extractSchemaLoad(self,loadFile:Path):
        #
        # Extract the Graph Name and Jobname from the defineSchema DDL file
        #
        lineCount = 0
        jobName = ""
        localGraphName = ""
        _dataFileDictonary = {}

        try:
            inFile = open(loadFile)

            for line in inFile:
                if (line.lower()).find("create") >=0 and (line.lower()).find("schema_change") >=0 :
                    commandLine = (line.lower()).split()
                    index = commandLine.index("graph")
                    command = line.split()
                    localGraphName = command[index+1]
                    jobName = command[index-2]

                lineCount +=1
            inFile.close

        except Exception as error:
            print("_extractSchemaLoad() Error:",error)

        #print("Number of Lines in File =", lineCount)

        _dataFileDictonary.update({"graphName" :localGraphName})
        _dataFileDictonary.update({"jobName" : jobName})

        return _dataFileDictonary


class SystemQuery:
    
    emptyResults=None
    valid_types = ['INT64','UINT','FLOAT','DOUBLE','BOOL','STRING', 'csv', 'json','terminal']

    def __init__(self,adminClass:CheetahServices):
        self.adminServices = adminClass
        self.configure = adminClass.configure

    def getQuerySummary(self,cache=None) -> dict:
        
        #subprocess.run('clear',shell=True)
        try:
            conn = self.adminServices.initConnection()


            if self.configure.getRemoteServer() and self.adminServices.localRemote == False:
                #print("\nRetreiving a list of Installed Queries on Remote Host to run:\n")
                url=f"{self.adminServices.host}/gsql/v1/queries?graph={self.adminServices.graphName}"
                results = conn._get(url, resKey=None, skipCheck=True)
                cache = results["results"]
            else:
                #print("\nRetreiving a list of Installed Queries on Local Host to run:\n")                
                url=f"{self.adminServices.host}:14240/gsql/v1/queries?graph={self.adminServices.graphName}"            
                results = conn._get(url, resKey=None, skipCheck=True)
                cache = results["results"]
        
        except Exception as error:
            print("getQuerySummary() Error:",error)
            return error

        return cache

    def displayInstalledQueries(self):

        foundQueries = False
        listOfQueries = []

        conn = self.adminServices.initConnection()
        results = conn.gsql("USE GRAPH "+conn.graphname+" ls")
        results = results.splitlines()

        for line in results:
            if foundQueries == True:
                index = line.find("- ")
                if (index > -1):
                    listOfQueries.append(line[index+2:len(line)])

            index = line.find("Queries:")
            if (index == 0):
                foundQueries = True

            index = line.find("Tags:")
            if (index == 0):
                foundQueries = False

        count = 0
        for query in listOfQueries:
            if len(query) > 0:
                count = count + 1
                print("(" + str(count) + ")",query)

    def createQueries(self,queryName=None):

        queryDir = self.configure.getDDLQueryDir()
        queryStatement = ''

        try:
            errorFlag = True
            conn = self.adminServices.initConnection()
            #
            # Create a indexed list of queries from the file system
            #
            if queryName == None:
                listDir = self.adminServices._listDDLFiles(queryDir)
                print('(0) Create All Queries...')
                while errorFlag == True:
                    index = input("Please select Query Option: ")
                    print("")
                    listIndex = index.split(',')
                    for index in listIndex:
                        if len(index) > 0 and index.isnumeric() == False:
                            errorFlag = True
                            break
                        else:
                            errorFlag = False

                if len(index) == 0:
                    return
                #
                # Install an Individual or a list of queries that the user selected
                #
                for index in listIndex:
                    index = int(index)
                    if index > 0 and index <= (len(listDir)):
                        queryStatement = "USE GRAPH "+ self.configure.getGraphName()+"\n"
                        fullQueryName = listDir[index-1]
                        fullQueryName = fullQueryName+".gsql"
                        print("Creating Query",fullQueryName)
                        #
                        # Read file and build a query statement that gets loaded
                        # via gsql statement
                        #
                        inFile = open(queryDir/Path(fullQueryName))
                        for line in inFile:
                            queryStatement = queryStatement + line

                        results = conn.gsql(queryStatement)
                        print("\n",results)
                        inFile.close()

                    elif index == 0:
                        queryName = self.adminServices.ALL_FILES
            #
            # Install all queries that are found in the DDLs/Queries directory
            #
            if queryName == self.adminServices.ALL_FILES:
                listDir = self.adminServices._listDDLFiles(queryDir,displayFiles=False)

                for query in listDir:
                    queryStatement = "USE GRAPH "+ self.configure.getGraphName()+"\n"
                    fullQueryName = query+".gsql"
                    inFile = open(queryDir/Path(fullQueryName))

                    for line in inFile:
                        queryStatement = queryStatement + line

                    results = conn.gsql(queryStatement)
                    print(results)
                    inFile.close()

            elif queryName != None:
                ix = queryName.find("[")
                if (ix < 0):
                    ix = len(queryName)

                print("Creating Query",queryName[:ix])
                queryStatement = "USE GRAPH "+ self.configure.getGraphName()+"\n"
                inFile = open(queryDir/Path(queryName+".gsql"))
                for line in inFile:
                    queryStatement = queryStatement + line

                results = conn.gsql(queryStatement)
                inFile.close()
                return results
        except Exception as error:
            print("createQueries() Error:",error)
            return error

        return results

    def installQueries(self,queryName=None):

        self.cachedQueries = {}
        queryDir = self.configure.getDDLQueryDir()
        listDir = None

        try:
            conn = self.adminServices.initConnection()
            errorFlag = True
            queryStatement = "USE GRAPH "+conn.graphname+" INSTALL QUERY "

            conn = self.adminServices.initConnection()

            if queryName == None:
                listDir = self.adminServices._listDDLFiles(queryDir)
                print('(0) Install All Queries...')
                while errorFlag == True:
                    index = input("Please select Query Option: ")
                    listIndex = index.split(',')
                    for index in listIndex:
                        if len(index) > 0 and index.isnumeric() == False:
                            errorFlag = True
                            break
                        else:
                            errorFlag = False

                if len(index) == 0:
                    return False

                for index in listIndex:
                    index = int(index)
                    if index > 0 and index <= (len(listDir)):
                        fullQueryName = listDir[index-1]
                        ix = fullQueryName.find("[")
                        if (ix < 0):
                            ix = len(fullQueryName)
                        fullQueryName = fullQueryName[:ix]
                        print("Installing Query",fullQueryName)
                        results = conn.gsql(queryStatement + fullQueryName, self.configure.getGraphName())
                        print("\n",results)
                    elif index == 0:
                        queryName = self.adminServices.ALL_FILES

            if queryName == self.adminServices.ALL_FILES:
                listDir = self.adminServices._listDDLFiles(queryDir,displayFiles=False)

                for query in listDir:
                    ix = query.find("[")
                    if (ix < 0):
                        ix = len(query)

                    print("Installing Query",query[:ix])
                    results = conn.gsql(queryStatement + query[:ix], self.configure.getGraphName())
                    print("\nQuery:", query,results,"\n")

            elif queryName != None:
                ix = queryName.find("[")
                if (ix < 0):
                    ix = len(queryName)

                print("Installing Query",queryName[:ix])
                results = conn.gsql(queryStatement + queryName[:ix], self.configure.getGraphName())
                print("\n",results)
                return True

        except Exception as error:
            print("installQueries() Error:",error)
        
        return True
    
    def deleteQueries(self,fullQueryName=None):

        queryDir = self.configure.getDDLQueryDir()
        queryStatement = "USE GRAPH "+ self.configure.getGraphName() +" DROP QUERY ALL"
        #
        # If no fullQueryName is specified, then print a list of queries
        #
        try:
            errorFlag = True
            conn = self.adminServices.initConnection()
            #
            # If no query name was passed in, then build
            # a list of queries from the DDLs/Queries directory
            #
            if fullQueryName == None:
                listDir = self.adminServices._listDDLFiles(queryDir)
                print('(0) Delete All Above...')
            elif fullQueryName == self.adminServices.ALL_FILES:
                print("Deleting All Queries for Graph: " + self.configure.getGraphName())
                gx = self.configure.getGraphName().find('Global')
                if (gx > 0):
                    ans = input("Are sure you want to drop ALL Queries accross ALL databases?...(y/n)")
                    if ans in ["y", "Y", "Yes", "yes"]:
                        results = conn.gsql(queryStatement)
                    else:
                        return
                else:
                    results = conn.gsql(queryStatement)
                print(results)
                return
            else:
                results = conn.gsql(queryStatement + fullQueryName, self.configure.getGraphName())
                print(results)
                return

            while errorFlag == True:
                index = input("Please select Query(s) to Delete: ")
                listIndex = index.split(',')
                for index in listIndex:
                    if len(index) > 0 and index.isnumeric() == False:
                        errorFlag = True
                        break
                    else:
                        errorFlag = False

            if index == '':
                return

            for index in listIndex:
                index = int(index)
                if index > 0 and index <= (len(listDir)):
                    queryStatement = f"USE GRAPH {self.configure.getGraphName()} DROP QUERY "
                    fullQueryName = listDir[index-1]
                    ix = fullQueryName.find("[")
                    if (ix < 0):
                        ix = len(fullQueryName)
                    fullQueryName = fullQueryName[:ix]
                    print("Deleting Query:",fullQueryName)
                    results = conn.gsql(queryStatement + fullQueryName, self.configure.getGraphName())
                    print("\n",results)
                elif index == 0:
                        ans = input("Are sure you want to drop ALL Queries...(y/n)")
                        if ans in ["y", "Y", "Yes", "yes"]:
                            print("Deleting All Queries...")
                            results = conn.gsql(queryStatement, self.configure.getGraphName())
                            print("\n",results)
                        else:
                            print("Cancelling 'Drop All Queries' Command...")

        except Exception as error:
            print("deleteQueries() Error:",error)
            return error


    def displayQueries(self):

        queryDir = self.configure.getDDLQueryDir()
        listDir = self.adminServices._listDDLFiles(queryDir)
        print('(0) Show All above...')

        try:
            queryStatement = "show query "

            conn = self.adminServices.initConnection()

            index = 'None'
            while index != '' and index.isnumeric() == False :
                index = input("Please select Query Option Display: ")

            if index == '':
                return
            else:
                index = int(index)

            if index > 0 and index <= (len(listDir)):
                fullQueryName = listDir[index-1]
                ix = fullQueryName.find("[")
                if (ix < 0):
                    ix = len(fullQueryName)
                fullQueryName = fullQueryName[:ix]
                results = conn.gsql(queryStatement + fullQueryName, self.configure.getGraphName())
                print("\n",results)
            elif index == 0:
                for query in listDir:
                    results = conn.gsql(queryStatement + query, self.configure.getGraphName())
                    print("\n",results)

        except Exception as error:
            print("showQueries() Error:",error)
            return error

    def queryByName(self):

        try:
            queryDir = self.configure.getDDLQueryDir()
            listDir = self.adminServices._listDDLFiles(queryDir)
            #print('(0) Create & Install All above...')

            index = 'None'
            while index != '' and index.isnumeric() == False :
                index = input("Please select Query Option to Create & Install: ")

            if index == '':
                return
            else:
                index = int(index)

            if index > 0 and index <= (len(listDir)):
                fullQueryName = listDir[index-1]
                results = self.createQueries(queryName=fullQueryName)
                if (results.find("Successfully") >= 0):
                    results=self.installQueries(fullQueryName)
                else:
                    print(f"Create Queries Error:\n{results}")
            elif index == 0:
                for query in listDir:
                    results = self.createQueries(queryName=query)

                    if (results.find("Successfully") >= 0):
                        results=self.installQueries(query)
                        print(results)
                    else:
                        print(f"Create Queries Error:\n{results}")                        

        except Exception as error:
            print("queryByName() Error:",error)


    def runQuery(self):

        count=0
        answer="Go"
        timeOutValue=60

        try:
            conn = self.adminServices.initConnection()            
            
            while len(answer) !=0 and answer.lower() != 'q' and answer.lower() != 'quit':
                self.emptyResults=False
                self.cachedQueries = self.getQuerySummary()
                #
                # Its possible that no queries are installed!
                #
                if len(self.cachedQueries) == 0:
                    print("No Queries Found...Have you installed any Queries?")
                    return False

                for query in self.cachedQueries:
                    print('  ('+str(count)+')',query)
                    count += 1
                print('  (x)',"To Return to Menu\n")
                count=0
                answer = input("Which Query would like to Run?: ")
                if len(answer) < 1 or answer in ['x', 'X', 'exit', 'quit', 'q']:
                    return "Exit"

                index = int(answer)
                if index > -1 and index <= (len(self.cachedQueries)-1):
                    queryName = self.cachedQueries[index]
                    parameters = self._getQueryMetaDataParameters(queryName)
                    
                    try:
                        inputParms = self._scanInputParams(parameters)
                        #
                        # Run Query with input Parameters
                        #
                        timeOutValue = int(inputParms.pop('timeout'))
                        results = conn.runInstalledQuery(queryName,inputParms,(timeOutValue*1000))
                        
                        self.emptyResults = self.isResultSetEmpty(queryName, results)
                        
                        if self.emptyResults == False:
                            if inputParms.get("format") == 'terminal':
                                print(f"{json.dumps(results, indent=4, separators=('. ', ' = '))}")                            
                            if inputParms.get("format") == 'csv':
                                outputFile = f"{self.configure.getOutputsDir()}/{queryName}.csv"
                                self.json_to_csv(results, outputFile)
                                print(f"\nWritting Query Results to {outputFile}")
                            elif inputParms.get("format") == 'json':
                                outputFile = f"{self.configure.getOutputsDir()}/{queryName}.json"
                                with open(outputFile, 'w', encoding='utf-8') as file:                                    
                                    json.dump(results, file, indent=4, separators=('. ', ' = '))
                                print(f"\nWritting Query Results to {outputFile}")

                    except LookupError as e:
                        print(f"Error in running query {queryName}, {e}")
                    except Exception as e:
                        print(f"Error writing to file {queryName}: {e}")
            
                input("\nPress Enter to continue: ")

        except Exception as error:
            print("runQuery() Error:",error)

    def json_to_csv(self, json_data, csv_filename):
        with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
                      
            # Extract all possible keys dynamically
            resultRow = list()
            for entry in json_data:
                self._writeCSV_header(writer, entry)
                self._writeCSV_values(writer, entry, resultRow)

    def _writeCSV_values(self, writer, entry, resultRow):
        try:
            for aResultSet in entry:
                anObject = entry.get(aResultSet)
                if isinstance(anObject,list):                    
                    for row in anObject:
                        resultRow = list()
                        if isinstance(row,dict):
                            if len(row.get("v_type",{})) > 0:
                                resultRow.append(row.get("v_type",{}))
                                for attr in row.get("attributes", {}).keys():
                                    value = row.get("attributes", {}).get(attr)
                                    if isinstance(value, list):
                                            # print('"' + ', '.join(map(str, value))+ '"')
                                        resultRow.append(', '.join(map(str, value)))
                                    else:
                                        resultRow.append(row.get("attributes", {}).get(attr))
                            elif len(row.get("e_type",{})) > 0:
                                for attr in row:
                                    if (attr == 'attributes'):
                                        resultRow.append(row.get("attributes", {}).get(attr))
                                    else:
                                        resultRow.append(row.get(attr))

                                    # Write row dynamically
                            else:
                                for attr in row:
                                    resultRow.append(row.get(attr))
                            
                            writer.writerow(resultRow)
                        else:
                            resultRow.append(row)
                            writer.writerow(resultRow)
                else:
                    resultRow.append(anObject)
                    writer.writerow(resultRow)
            writer.writerow([])
        except Exception as e:
            print(f"Error in _writeCSV_values:")
            #traceback.print_exc()

    def _writeCSV_header(self, writer, entry):
        try:
            header_keys = list()
            for aResultSet in entry:
                anObject = entry.get(aResultSet)
                if isinstance(anObject,list):
                    for row in anObject:
                        if isinstance(row,dict):
                            if len(row.get("v_type",{})) > 0:
                                header_keys.append("v_type")
                                for attr in row.get("attributes", {}).keys():
                                    header_keys.append(attr)
                            elif len(row.get("e_type",{})) > 0:
                                for attr in row:
                                    if (attr == 'attributes'):
                                        for attr in row.get("attributes", {}).keys():
                                            header_keys.append(attr)
                                    else:
                                        header_keys.append(attr)
                            else:
                                for attr in row:
                                    header_keys.append(attr)
                        else:
                            header_keys.append(aResultSet)
                        break
                else:
                    header_keys.append(aResultSet)

                    # Write header row
            writer.writerow(header_keys)
        except Exception as e:
            print(f"Error in _writeCSV_header:")
            #traceback.print_exc()

    def isResultSetEmpty(self, queryName, results):
        if len(results) == 0:
            print(f"No output found for query {queryName}...")
            self.emptyResults=True
                        
        if not self.emptyResults:
            for dic in results:
                for key in dic.keys():
                    value = dic.get(key)
                    if isinstance(value, (str, list, dict, set)):
                        self.emptyResults = not bool(value)
                    else:
                        self.emptyResults = (value == 0)
                            
            if self.emptyResults:        
                print(f"No output found for query {queryName}...")
        return self.emptyResults

    def _scanInputParams(self, inputParameters):
        
        inputValues = {}
        for param in inputParameters:
            for key in param.keys():

                if param.get(key) in self.valid_types:
                    found=False
                    if (key == 'format'):
                        ans = prompt("Please enter in Output Format (terminal, json or csv):",default=param.get(key))
                        inputValues[key]=ans.lower()
                        found = True                     
                    elif (param.get(key) =='BOOL'):
                        ans = prompt("Please enter in " + key + " ("+param.get(key) + "):",default="True")
                        inputValues[key]=ans
                        found = True
                    elif (param.get(key) =='UINT'):
                        if (key == 'timeout'):
                            ans = prompt("Please enter in Query Timeout Value (default in Seconds):",default=self.configure.getQueryTimeout())
                            inputValues[key]=ans
                            found = True
                        else:
                            inputValues[key]=ans
                            found = False

                    elif (found == False):
                        ans = prompt("Please enter in " + key + " ("+param.get(key) + "):")
                                
                    if (param.get(key) =='STRING'):
                        inputValues[key]=ans
                    elif (param.get(key) =='INT64' and len(ans) > 0):
                        inputValues[key]=ans
                    elif (param.get(key) =='FLOAT' and len(ans) > 0):
                        inputValues[key]=ans
                    elif (param.get(key) =='DOUBLE' and len(ans) > 0):
                        inputValues[key]=ans                
                else:
                    raise LookupError(f"{param.get(key)} is not a valid Primitive Type that can be passed on the command line...")
        return inputValues
    
    def _getQueryMetaData(self, queryName):
        try:
            conn = self.adminServices.initConnection()

            if self.configure.getRemoteServer() and self.adminServices.localRemote == False:
                url=f"{self.adminServices.host}/gsql/v1/queries/info?graph={self.configure.getGraphName()}&query={queryName}"
            else: #local Server
                url=f"{self.adminServices.host}:14240/gsql/v1/queries/info?graph={self.configure.getGraphName()}&query={queryName}"
            results = conn._get(url, resKey=None, skipCheck=True)        
        except Exception as e:
            print(f"_getQueryMetaData {queryName}: {e}")

        return results

    def _getQueryMetaDataParameters(self, queryName):
        try:
            conn = self.adminServices.initConnection()

            if self.configure.getRemoteServer() and self.adminServices.localRemote == False:
                url=f"{self.adminServices.host}/gsql/v1/queries/info?graph={self.configure.getGraphName()}&query={queryName}"            
            else: #local Server
                url=f"{self.adminServices.host}:14240/gsql/v1/queries/info?graph={self.configure.getGraphName()}&query={queryName}"
            results = conn._get(url, resKey=None, skipCheck=True)        
        except Exception as e:
            print(f"_getQueryMetaData {queryName}: {e}")

        dic = results['results'][0]
        if len(dic.get('callerQueries')) > 0:
            callerQueries = dic.get('callerQueries')[0]
            raise LookupError(f"Query {queryName} is called from {callerQueries} query. Please call {callerQueries} to run this query...")

        tempParameters = dic.get('endpoint').get('query').get(self.configure.getGraphName()).get(queryName).get('GET/POST').get('parameters')
        tempList = []
        for params in tempParameters:
            if params != 'query':
                value = tempParameters.get(params)
                if "id_type" in value:
                    type = value.get("id_type")
                else:
                    type = value.get("type")
                tempList.append({params:type})
        
        tempList.append({'format':self.configure.getDisplayFormat()})
        tempList.append({'timeout':'UINT'})
        #tempList.append({'format':'terminal'}) 
        return tempList

    def forkQuerySummary(self,cache):
        try:
            pid = os.fork()
            if pid > 0:
                #sys.exit(0)
                time.sleep(.5)
        except OSError as e:
            print >>sys.stderr, "fork #1 failed: %d (%s)" % (e.errno, e.strerror)
            sys.exit(1)

        #os.chdir("/")
        #os.setsid( )
        #os.umask(0)
        if pid == 0:
            self.getQuerySummary(cache)
            print("\nQuery Cache Update Completed...")


            #sys.exit(0)
            #print(results)

class SystemSecrets:

    def __init__(self,adminClass:CheetahServices):
        self.adminServices = adminClass
        self.configure = adminClass.configure

    #
    # Create a Secret and Token for remote connection for 30 days (default)
    #
    def createSecret(self, aliasName,expirationDate=2592000):

        update_Flag = False
        try:
            if (len(aliasName) > 0):
                if (self.getAliasExists(aliasName) == False):
                    self._secret = self.adminServices.getConnection().createSecret(alias=aliasName)
                    update_Flag=True
                    self._token = ""
                    self.configure.setSecret(self._secret)
                    print("Secret =",self._secret)
                else:
                    raise LookupError("Secret Already exists. If you want to create a new Secret, please delete this Secret...")
            #
            # Create a token with default of 30 day expiration
            #
            if (len(self._secret) > 0):
                tokenTuple = self.adminServices.getConnection().getToken(None,lifetime=int(expirationDate))
                update_Flag=True
                self._token = tokenTuple[0]
                #self._token = tokenTuple
                self.configure.setToken(self._token)
                self._tokenExpirationDate = tokenTuple[1]
                self.configure.setTokenExpirationDate(self._tokenExpirationDate)
                print(f"New Token = {tokenTuple[0]}")
                print(f"Expiration Date = {tokenTuple[1]}")

            else:
                self._token = self.configure.getToken()
                self.adminServices.getConnection().apiToken = self._token

            if update_Flag == True and aliasName == self.configure.getSecretAlias():
                self.configure.writeTGAdminConf()

        except LookupError as error:
            print("Error:",repr(error))
            input("\nPress Enter to continue: ")
            return False

        except Exception as error:
            print("createSecret/Token Error:",repr(error))
            #traceback.print_exc()
            input("\nPress Enter to continue: ")
            return False

        return True
    
    def deleteSecret(self, aliasName):

        try:
            conn = self.adminServices.initConnection()
            reqStatus = conn.gsql("USE GRAPH "+conn.graphname+" DROP SECRET " + aliasName)
            if reqStatus.find("Error") < 0:
                if aliasName == self.configure.getSecretAlias():
                    self.configure.setSecret("")
                    self.configure.setToken("")
                    self.configure.setTokenExpirationDate("")
                    self.configure.writeTGAdminConf()
                    print("deleteSecrets() for",aliasName,"was succussful...")
            else:
                print("deleteSecrets() Error...", reqStatus)
        except Exception as error:
            print("deleteSecrets() Error...", repr(error))

    def displaySecrets(self,display=True):

        autoAlias = ''
        timeStamp = ''
        secret = ''
        aliasSuffix = self.configure.getSecretAlias()
        self.foundAlias = False
        try:
            conn = self.adminServices.initConnection()
            results = conn.getSecrets()
            version = self.configure.getVersion()

            if self.adminServices.isICloud(version):
                for key in results.keys():
                    if key == aliasSuffix:
                        foundAliasName = key
                        self.foundAlias = True
                        secret = results.get(key)
                        timeStamp = self.configure.getTokenExpirationDate()
                        break
            else:
                results = conn.gsql("USE GRAPH "+conn.graphname+" SHOW SECRET")     
                sentences = results.split("\n")
                for line in sentences:
                    if line.find(aliasSuffix) >= 0:
                        self.foundAlias = True
                        index = line.find(aliasSuffix)
                        foundAliasName = line[index:]
                    if line.find("expire at:") >= 0:
                        timeIndex = line.find("expire at: ")
                        timeStamp = line[timeIndex+11:len(line)]
                    elif line.find("AUTO_GENERATED_ALIAS") >=0:
                        index = line.find("AUTO_GENERATED_ALIAS")
                        autoAlias = line[index:]

            if len(autoAlias) >0 and display == False:
                reqStatus = conn.gsql("USE GRAPH "+conn.graphname+" DROP SECRET " + autoAlias)
                print(reqStatus)
            #
            # Configuration File out of Sync with Database, Delete and Start over
            #
            if self.foundAlias == True and len(self.configure.getSecret()) == 0:
                reqStatus = conn.gsql("USE GRAPH "+conn.graphname+" DROP SECRET " + foundAliasName)
                if (reqStatus.find("Success") < 0):
                    raise Exception("displaySecrets() Error: Can't DROP SECRET...")

                self.foundAlias = False

            if self.foundAlias == False:
                if display == False:
                    #raise LookupError("\nYour Config File is out of Sync with your Secrets for Graph: "+self.graphName+", Remove the secret & token from your config file...")
                    return False
                else:
                    print(f"\nNo Secrets found for Graph: {self.adminServices.graphName}, Your Config File may be of Sync with your Secrets. Remove the secret & token from your config file...")
            elif display == True:
                if self.adminServices.isICloud(version):
                    print (f"Alias = {foundAliasName}")
                    print (f"Secret = {secret}")
                    print (f"Expration Date: {timeStamp}")
                    timenow = datetime.now()
                    timeLeft = timeStamp - timenow
                    print ("Time Left on " +self.configure.getSecretAlias() +" Token =",timeLeft.days,"Days")
                else:
                    print(results)
                    timenow = datetime.now()
                    expTime = datetime.strptime(timeStamp, '%Y-%m-%d %H:%M:%S')
                    self.configure.setTokenExpirationDate(timeStamp)
                    self.configure.writeTGAdminConf()
                    timeLeft = expTime - timenow
                    print ("Time Left on " +self.configure.getSecretAlias() +" Token =",timeLeft.days,"Days")
        except Exception as err:
            print(f"Error in Display Secerts {err}")
            #traceback.print_exc()

        return self.foundAlias

    def installSecrets(self, processing_global_variables):
        results = self.hasExistingSecrets()
        if results == False and processing_global_variables == False:
            rs = self.createSecret(self.configure.getSecretAlias())
            if (rs == True):
                print("\n******* Warning *******")
                print("Make sure to store the Secret & Token values in a safe plase, Once you hit enter, you will not be able to retrieve these values")

        else:
            print(f"Secrets already exist for {self.configure.getSecretAlias()}...")
            print(f"Token Experation is: {self.configure.getTokenExpirationDate()}")

        #
        # Now that we have a token, update the version number
        #
        if (self.configure.getVersion() == None):
            versionNumber = self.adminServices.extractVersionNumber()
            self.configure.setVersion(versionNumber)
            self.configure.writeTGAdminConf()


    def refreshToken(self,secret,token,refreshTime):
        try:

            if (secret == None and token == None):
                currentDate = datetime.now()
                currentTime = calendar.timegm(currentDate.timetuple())
                token = self.configure.getToken()
                secret = self.configure.getSecret()
                tokenTuple = self.adminServices.getConnection().refreshToken(secret=secret,token=token,lifetime=refreshTime)
                print(f"Updated Token: {tokenTuple[0]}")
                self.configure.setToken(tokenTuple[0])
                newTime = refreshTime + currentTime + 86400
                newDate = datetime.fromtimestamp(newTime)
                timeLeft = (newDate - currentDate)
                self.configure.setTokenExpirationDate(datetime.fromtimestamp(newTime).strftime("%Y-%m-%d"))
                self.configure.writeTGAdminConf()
                #expTime = self.configure.getTokenExpirationDate()
        
                print ("Time Left on Existing Token =",timeLeft.days,"Days")
            elif secret != "" and token != "":
                if type(refreshTime) == int:
                    tokenTuple = self.adminServices.getConnection().refreshToken(secret=secret,token=token,lifetime=refreshTime)
                    print(tokenTuple)
        except Exception as err:
            print(f"Error in refresh Token {err}")


    def hasExistingSecrets(self):

        try:
            hasExistingSecret = self.displaySecrets(display=False)
            return hasExistingSecret

        except Exception as error:
                print("Error Checking Existing of Secrets...",error)
                return False

    def removeExpiredToken(self):
        try:
            conn = self.adminServices.initConnection()
            results = conn.gsql("USE GRAPH "+conn.graphname+" DELETE expiredtoken")
            print(results)
        except Exception as error:
            print("removeExpiredToken Error...", repr(error))

    def getAliasExists(self,aliasName):
        self.foundAlias = False
        conn = self.adminServices.initConnection()
        results = conn.gsql("USE GRAPH "+conn.graphname+" SHOW SECRET")
        sentences = results.split("\n")
        for line in sentences:
            if line.find(aliasName) >= 0:
                self.foundAlias = True
                index = line.find(aliasName)
                foundAliasName = line[index:]
                print(f"Alais Name {foundAliasName}")
                break

        return self.foundAlias


class SystemUtilities:

    def __init__(self,adminClass:CheetahServices):
        self.adminServices = adminClass
        self.configure = adminClass.configure
        self.systemPlatform = self.configure.systemPlatform

    def displayAllJobs(self) -> bool:

        try:
            conn = self.adminServices.initConnection()
            #url=self.configure.getHost()+f":14240/gsql/v1/loading-jobs/status"
            #results = conn._post(url, resKey=None, skipCheck=True)
            results = conn.gsql("USE GRAPH "+conn.graphname+" SHOW LOADING STATUS ALL")
            print(results)
            if results.find("aborted") >=0:
                return True
            else:
                return False
        except Exception as error:
            print(f"ERROR in Aborting Jobs: {error}")

    def abortAllJobs(self) -> bool:

        try:
            conn = self.adminServices.initConnection()
            #url=self.configure.getHost()+f":14240/gsql/v1/loading-jobs/status/all"
            #results = conn._post(url, resKey=None, skipCheck=True)
            results = conn.gsql("USE GRAPH "+conn.graphname+" ABORT LOADING JOB ALL")
            print(results)
            if results.find("aborted") >=0:
                return True
            else:
                return False
        except Exception as error:
            print(f"ERROR in Aborting Jobs: {error}")


    def checkGraphExists(self) -> bool:

      try:
            self.adminServices.initConnection()
            return self.adminServices.getConnection().check_exist_graphs(self.adminServices.getConnection().graphname)
      except Exception as e:
        print("Error Checking Graph Status: ", e)
        #traceback.print_exc()
        return False

    #
    # Display all the components version numbers
    # Note: you need a valid Secret / Token to call the getVersion() function
    #
    def displayComponentVersion(self):
        try:
            results = self.adminServices.getConnection().getVersion()
            print("\n")
            for cmp in results:
                print("%-21s %25s %25s %25s" % (cmp.get('name'),cmp.get('version'),cmp.get('hash'),cmp.get('datetime')) )

        except Exception as err:
             print(f"Error on Get Version Call.. {err}")
             print("Please create a Secret/Token to view database Version...")

    def displayCPUMemoryStatus(self):
        try:
 
            #url=self.configure.getHost()+":14240//informant/metrics/get/diskspace"
            #_serviceDescriptor = {"LatestNum":"1"} 
            #results = conn._post(url, data=json.dumps(_serviceDescriptor), resKey=None, skipCheck=True)

            results = self.adminServices.initConnection().getSystemMetrics(latest=1,what='cpu-memory') 
            #print(results)

            print("\nCPU & Memory Utilitzation Report\n")

            print(f"{'Service':17s} {'CPU Usage':12s} {'Memory Usage':11s}")
            print("-" * 43)
            for aMetric in results.get('CPUMemoryMetrics'):
                service = aMetric.get('ServiceDescriptor').get('ServiceName')
                cpu = aMetric.get('CPU').get('CPUUsage')
                memory = aMetric.get('Memory').get('MemoryUsageMB')
                cpu = 0 if cpu == None else cpu
                
                #print("%-15s %12s %11s MB" % (service, cpu, memory))
                print(f"{service:15s} {cpu:11,.5f} {memory:12,.0f} MB")
                #print(f"Service: {service}")
                #print(f"CPU Usage: {cpu}")
                #print(f"Memory Usage: {memory} MB \n")


        except Exception as error:
             print(f"Error on Display Cpu/Memory Status: {error}")

    def displayDiskStatus(self):
        try:
 
            #url=self.configure.getHost()+":14240//informant/metrics/get/diskspace"
            #_serviceDescriptor = {"LatestNum":"1"} 
            #results = conn._post(url, data=json.dumps(_serviceDescriptor), resKey=None, skipCheck=True)

            results = self.adminServices.initConnection().getSystemMetrics(latest=1,what='diskspace') 
            #print(results)

            totalDiskSpace = 0
            diskSpaceUsed = 0
            diskSpaceFree = 0
            print("\nDisk Space Utilitzation Report\n")

            for aMetric in results.get('DiskMetrics'):
                disk = aMetric.get('Disk')
                print(f"Path Name: {disk.get('PathName')}")
                print(f"Path: {disk.get('Path')}")
                print(f"Size: {disk.get('SizeMB'):,.2f} MB\n")
                diskSpaceUsed += disk.get('SizeMB')
                diskSpaceFree = disk.get("FreeSizeMB")

            totalDiskSpace = diskSpaceUsed + diskSpaceFree
            print(f"Disk Space Used: {diskSpaceUsed/1000:,.2f} GB")
            print(f"Disk Space Free: {diskSpaceFree/1000:,.2f} GB")
            print(f"Total Disk Space Allocated: {totalDiskSpace/1000:,.2f} GB")


        except Exception as error:
             print(f"Error on Display Disk Status for iCloud Version {error}")

    def displayServicesStatus(self):
        try:
            conn = self.adminServices.initConnection()
            url=self.configure.getHost()+":443/informant/current-service-status"
            _serviceDescriptor = {"ServiceDescriptors": [ {"ServiceName":"GPE"},
                                                          {"ServiceName":"GSE"},
                                                          {"ServiceName":"RESTPP"},
                                                          {"ServiceName":"GSQL"},
                                                          {"ServiceName":"IFM"},
                                                          {"ServiceName":"GUI"},
                                                          {"ServiceName":"CTRL"},
                                                          {"ServiceName":"KAFKA"},
                                                          {"ServiceName":"ETCD"},
                                                          {"ServiceName":"ZK"},
                                                          {"ServiceName":"NGINX"},
                                                          {"ServiceName":"TS3"},
                                                          {"ServiceName":"TS3SERV"},
                                                          {"ServiceName":"DICT"},
                                                          {"ServiceName":"ADMIN"}
                                                           ]}

            results = conn._post(url, data=json.dumps(_serviceDescriptor), resKey=None, skipCheck=True)
            for se in results["ServiceStatusEvents"]:
                sd = se["ServiceDescriptor"]
                serviceName = sd["ServiceName"]
                serviceStatus = se["ServiceStatus"]
                processState = se["ProcessState"]
                print("%-8s %7s %7s" % (serviceName, serviceStatus, processState) )
        except Exception as error:
            print("displayServicesStatus() Error:",error)
            #print(results['Error']['Message'])
            
    def displayDetailedServicesStatus(self):
        try:
            conn = self.adminServices.initConnection()
            url=self.configure.getHost()+":443/informant/current-service-status"
            _serviceDescriptor = {"ServiceDescriptors": [ {"ServiceName":"GPE"},
                                                          {"ServiceName":"GSE"},
                                                          {"ServiceName":"RESTPP"},
                                                          {"ServiceName":"GSQL"},
                                                          {"ServiceName":"IFM"},
                                                          {"ServiceName":"GUI"},
                                                          {"ServiceName":"CTRL"},
                                                          {"ServiceName":"KAFKA"},
                                                          {"ServiceName":"ETCD"},
                                                          {"ServiceName":"ZK"},
                                                          {"ServiceName":"NGINX"},
                                                          {"ServiceName":"TS3"},
                                                          {"ServiceName":"TS3SERV"},
                                                          {"ServiceName":"DICT"},
                                                          {"ServiceName":"ADMIN"}
                                                           ]}

            results = conn._post(url, data=json.dumps(_serviceDescriptor), resKey=None, skipCheck=True)
            for se in results["ServiceStatusEvents"]:
                sd = se["ServiceDescriptor"]
                serviceName = sd["ServiceName"]
                serviceStatus = se["ServiceStatus"]
                processState = se["ProcessState"]
                print("%-8s %7s %7s" % (serviceName, serviceStatus, processState) )

            print("\nDisplaying Detailed Server status:")
            #results = conn.gsql("USE GLOBAL ls")
            results = conn.gsql("USE GRAPH "+conn.graphname+" ls")

            print(results)

        except Exception as error:
            print("displayDetailedServicesStatus() Error:",error)
            #print(results['Error']['Message'])

    def displayServicesStatusiCloud(self):
        try:
            conn = self.adminServices.initConnection()
            if self.configure.getRemoteServer() and self.adminServices.localRemote == False:            
                url=self.configure.getHost()+"/informant/current-service-status"
            else:
                url=self.configure.getHost()+":14240/informant/current-service-status"
            
            _serviceDescriptor = {"ServiceDescriptors": [ {"ServiceName":"ADMIN"},
                                                          {"ServiceName":"CTRL"},
                                                          {"ServiceName":"DICT"},
                                                          {"ServiceName":"ETCD"},
                                                          {"ServiceName":"EXE"},
                                                          {"ServiceName":"GPE"},
                                                          {"ServiceName":"GSE"},
                                                          {"ServiceName":"GSQL"},
                                                          {"ServiceName":"GUI"},
                                                          {"ServiceName":"IFM"},
                                                          {"ServiceName":"KAFKA"},
                                                          {"ServiceName":"KAFKACONN"},
                                                          {"ServiceName":"KAFKASTRM-LL"},
                                                          {"ServiceName":"NGINX"},
                                                          {"ServiceName":"RESTPP"},
                                                          {"ServiceName":"ZK"}
                                                        ]}

            results = conn._post(url, data=json.dumps(_serviceDescriptor), resKey=None, skipCheck=True)
            for se in results["ServiceStatusEvents"]:
                sd = se["ServiceDescriptor"]
                serviceName = sd["ServiceName"]
                serviceStatus = se["ServiceStatus"]
                processState = se["ProcessState"]
                print("%-12s %8s %7s" % (serviceName, serviceStatus, processState) )
        
        except Exception as error:
            print("displayServicesStatusiCloud() Error:",error)
            print(results['Error']['Message'])

    def displayDetailedServiceStatusiCloud(self):
        try:
            conn = self.adminServices.initConnection()
            if self.configure.getRemoteServer() and self.adminServices.localRemote == False:            
                url=self.configure.getHost()+"/informant/current-service-status"
            else:
                url=self.configure.getHost()+":14240/informant/current-service-status"
            
            _serviceDescriptor = {"ServiceDescriptors": [ {"ServiceName":"ADMIN"},
                                                          {"ServiceName":"CTRL"},
                                                          {"ServiceName":"DICT"},
                                                          {"ServiceName":"ETCD"},
                                                          {"ServiceName":"EXE"},
                                                          {"ServiceName":"GPE"},
                                                          {"ServiceName":"GSE"},
                                                          {"ServiceName":"GSQL"},
                                                          {"ServiceName":"GUI"},
                                                          {"ServiceName":"IFM"},
                                                          {"ServiceName":"KAFKA"},
                                                          {"ServiceName":"KAFKACONN"},
                                                          {"ServiceName":"KAFKASTRM-LL"},
                                                          {"ServiceName":"NGINX"},
                                                          {"ServiceName":"RESTPP"},
                                                          {"ServiceName":"ZK"}
                                                        ]}

            results = conn._post(url, data=json.dumps(_serviceDescriptor), resKey=None, skipCheck=True)
            for se in results["ServiceStatusEvents"]:
                sd = se["ServiceDescriptor"]
                serviceName = sd["ServiceName"]
                serviceStatus = se["ServiceStatus"]
                processState = se["ProcessState"]
                print("%-12s %8s %7s" % (serviceName, serviceStatus, processState) )

            print("\nDisplaying Detailed Server status:")
            #results = conn.gsql("USE GLOBAL ls")
            results = conn.gsql("USE GRAPH "+conn.graphname+" ls")

            print(results)

        except Exception as error:
            print("displayDetailedServerStatusiCloud() Error:",error)
            print(results['Error']['Message'])
