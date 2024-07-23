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

def readFile(fileName):
    print("readFile()")
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
    for n in range(1,df['RNTI'].max()+1):
        r = a[a['RNTI']==n]
        for i in range(len(r.index)):
            rbg = r.iloc[i]['RBG']
            # print(rbg)
            for rb in range(len(rbg)):
                if rbg[rb]==1:
                    for x in range(r.iloc[i]['Num Sym']):
                        slot.loc[r.iloc[i]['Start Sym']+x,rb] = r.iloc[i]['RNTI']

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
    RBGRange = len(df.iloc[0])-2
    print("Range:{}".format(RBGRange))
    print(df)
    row = df.iloc[0]
    print(row)
    for i in range(RBGRange):
        Pulse = plt.Rectangle((xIndex, yIndex), boxWidth, boxHeight, fill=True,edgecolor='b',facecolor='r') 
        ax.add_patch(Pulse)
        # Index += RadarPW + RadarPRI_s
        xIndex += boxWidth
    return

def main():
    print("main()")
    # df = readFile('simulationLogs.mat')
    # df = mergeAll(df)
    # df.to_pickle('tmp.pkl')
    df = pd.read_pickle('tmp.pkl')
    fig = plt.figure(figsize=(25,5)) 
    ax = fig.add_subplot(1, 1, 1)
    ax.set_xlim(0,10)
    ax.set_ylim(-10,10) 
    plotRBGrid(ax,df)
    plt.savefig('plt.jpeg')
if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()