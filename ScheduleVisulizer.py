#!/usr/bin/python3
#Script Used to graph 5G TDD slot patterns, and calculate symbol interfeerence based on radar charcterisitics. 
__author__ = "Eric Forbes"
__version__ = "0.1.0"
__license__ = "MIT"
import scipy.io
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt 
import matplotlib.patches as patches

symbolsPerSlot = 14

#Colors
cDeflt = 'w'
c1 = 'r'
c2 = 'b'
c3 = 'g'
c4 = 'y'

def readSimParamFile(fileName):
    print('readSimParamFile()')
    mat = scipy.io.loadmat(fileName)
    NumFramesSim = mat['simParameters']['NumFramesSim'][0][0][0][0]
    SchedulingType = mat['simParameters']['SchedulingType'][0][0][0][0]
    NumUEs = mat['simParameters']['NumUEs'][0][0][0][0]

    print(NumFramesSim,SchedulingType,NumUEs)
    df = pd.DataFrame()
    return df

def readSimLogFile(fileName):
    print("readSimLogFile()")
    mat = scipy.io.loadmat(fileName)
    
    #pull the relevant arrary from
    simLogs = mat['simulationLogs']
    simLogs = simLogs[0][0]['SchedulingAssignmentLogs'][0][0]
    
    #convert to DataFrame
    df = pd.DataFrame(simLogs)
    
    #Remove array chars
    for i in range(15):
        df[i] = df[i].astype(str).str.replace('[','')
        df[i] = df[i].astype(str).str.replace(']','')
        df[i] = df[i].astype(str).str.replace('\'','')
        df[i] = df[i].astype(str).str.replace(';',' ')
    
    #make new DF with the right column
    header = df.iloc[0]
    df  = pd.DataFrame(df.values[1:], columns=header)
    # print(header)
    df = df.rename(columns={'RBG Allocation Map':'RBG',
                            'Feedback Slot Offset (DL grants only)':'FdbkOffst',
                            'CQI on RBs':'CQIs'})
    
    #convert relevant columns to the right types
    toInts = ['RNTI','Frame','Slot','Start Sym', 'Num Sym', 'MCS', 'NumLayers', 'HARQ ID', 'NDI Flag', 'RV']
    #--INTS
    for i in toInts:
        df[i] = pd.to_numeric(df[i])
    toStrs = ['Grant type','Tx Type']
    #--Strings
    for i in toStrs:
        df[i] = df[i].astype(str)
    #--ARRAYS
    df['RBG'] = df['RBG'].astype(str).str.split(pat=' ')
    df['RBG'] = df['RBG'].apply(lambda lst: list(map(int, lst)))
    df['CQIs'] = df['CQIs'].astype(str).str.split(pat=' ')
    df['CQIs'] = df['CQIs'].apply(lambda lst: list(map(int, lst)))

    return df

def mergeRBG(df,frameIdx,slotIdx):
    print('mergeRBG(df,{},{})'.format(frameIdx,slotIdx))
    a = df[(df['Frame']==frameIdx) & (df['Slot']==slotIdx)]
    if a.empty: return a
    slot = pd.DataFrame(0,index=np.arange(symbolsPerSlot), columns=np.arange(len(a.iloc[1]['RBG'])))
    slot.insert(0,"Frame",frameIdx)
    slot.insert(1,"Slot",slotIdx)
    slot.insert(2,'Type',0)
    for n in range(1,df['RNTI'].max()+1):
        r = a[a['RNTI']==n]
        for i in range(len(r.index)):
            rbg = r.iloc[i]['RBG']
            # print(rbg)
            for rb in range(len(rbg)):
                if rbg[rb]==1:
                    for x in range(r.iloc[i]['Num Sym']):
                        slot.loc[r.iloc[i]['Start Sym']+x,rb] = r.iloc[i]['RNTI']
                        # slot.loc[r.iloc[i]['Start Sym']
    return slot

def mergeAll(df):
    merged = []
    for i in range(0,df['Frame'].max()):
        x = 1 if i==0 else 0
        for j in range(x,10):
            data = mergeRBG(df,i,j)
            if not data.empty:
                merged.append(mergeRBG(df,i,j))
    df = pd.concat(merged,ignore_index=True)
    print(df)
    return df

def plotRBGrid(ax,df):
    print("plotRBGrid()")
    xIndex = 0
    yIndex = 0
    boxWidth = 1
    boxHeight = 1
    RBGRange = len(df.iloc[0])-3
    print("Range:{}".format(RBGRange))
    print(df)
    for rowIdx in range(len(df.index)):
        row = df.iloc[rowIdx]
        for i in range(0,RBGRange):
            match row[i]:
                case 1:
                    idxColor = c1
                case 2: 
                    idxColor = c2
                case 3:
                    idxColor = c3
                case 4:
                    idxColor = c4
                case _:
                    idxColor = cDeflt
            Pulse = plt.Rectangle((xIndex, yIndex), boxWidth, boxHeight, fill=True,edgecolor='black',facecolor=idxColor) 
            ax.add_patch(Pulse)
            # Index += RadarPW + RadarPRI_s
            xIndex += boxWidth
        yIndex -= boxHeight
        xIndex = 0
    return

def main():
    print("main()")
    simParams = readSimParamFile('simParameters.mat')
    return
    df = readSimLogFile('simulationLogs.mat')
    print(df)
    df = mergeAll(df)
    df.to_pickle('tmp.pkl')
    df = pd.read_pickle('tmp.pkl')
    # df.to_csv('tmp.csv')
    fig = plt.figure(figsize=(4,100)) 
    ax = fig.add_subplot(1, 1, 1)
    ax.set_xlim(0,9)
    ax.set_ylim(-1000,0) 
    plotRBGrid(ax,df)
    plt.subplots_adjust(left=0.1, right=.97, top=0.99, bottom=0.01)
    plt.savefig('plt.jpeg')
if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()