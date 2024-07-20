#!/usr/bin/python3
#Script Used to graph 5G TDD slot patterns, and calculate symbol interfeerence based on radar charcterisitics. 
__author__ = "Eric Forbes"
__version__ = "0.1.0"
__license__ = "MIT"
import scipy.io
import pandas as pd

def readFile(fileName):
    mat = scipy.io.loadmat(fileName)
    
    #pull the relevant arrary from
    simLogs = mat['simulationLogs']
    simLogs = simLogs[0][0]['SchedulingAssignmentLogs'][0][0]
    
    #convert to DataFrame
    df = pd.DataFrame(simLogs)
    removals  = '|'.join(['[', ']'])
    for i in [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14]:
        df[i] = df[i].astype(str).str.replace('[','')
        df[i] = df[i].astype(str).str.replace(']','')
        df[i] = df[i].astype(str).str.replace('\'','')
    header = df.iloc[0]
    df  = pd.DataFrame(df.values[1:], columns=header)
    # df["rnti"] = pd.to_numeric(df["rnti"])
    return df

def main():
    print("Main()")
    df = readFile('simulationLogs.mat')
    print(df)
if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()