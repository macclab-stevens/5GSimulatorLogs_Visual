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
from matplotlib.offsetbox import AnchoredText
from datetime import datetime

symbolsPerSlot = 14

#Colors
cDeflt = 'w'
rntiColors = [
'w',
'r',
'b',
'g',
'y']


class simParameters:
    def __init__(self,fileName) -> None:
        print('class simParameters __init__')
        mat = scipy.io.loadmat(fileName)
        self.NumFramesSim = mat['simParameters']['NumFramesSim'][0][0][0][0]
        self.SchedulingType = mat['simParameters']['SchedulingType'][0][0][0][0]
        self.NumUEs = mat['simParameters']['NumUEs'][0][0][0][0]
        self.NumRBs = mat['simParameters']['NumRBs'][0][0][0][0]
        self.SCS = mat['simParameters']['SCS'][0][0][0][0]
        self.DLBandwidth = mat['simParameters']['DLBandwidth'][0][0][0][0]
        self.ULBandwidth = mat['simParameters']['ULBandwidth'][0][0][0][0]
        self.DLCarrierFreq = mat['simParameters']['DLCarrierFreq'][0][0][0][0]
        self.ULCarrierFreq = mat['simParameters']['ULCarrierFreq'][0][0][0][0]
        self.NumDLSlots = mat['simParameters']['NumDLSlots'][0][0][0][0]
        self.NumDLSyms = mat['simParameters']['NumDLSyms'][0][0][0][0]
        self.NumULSyms = mat['simParameters']['NumULSyms'][0][0][0][0]
        self.NumULSlots = mat['simParameters']['NumULSlots'][0][0][0][0]
        self.SchedulerStrategy = mat['simParameters']['SchedulerStrategy'][0][0][0]
        self.TTIGranularity = mat['simParameters']['TTIGranularity'][0][0][0][0]
        self.RBAllocationLimitUL = mat['simParameters']['RBAllocationLimitUL'][0][0][0][0]
        self.RBAllocationLimitDL = mat['simParameters']['RBAllocationLimitDL'][0][0][0][0]
        


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

def slotType(slot,slotIdx,params):
    if slotIdx >=5: slotIdx -= 5
    if slotIdx < params.NumDLSlots: #DL SLOTS
        print("Slot:{}, Type:{}".format(slotIdx,"DL"))
        slot['Type'] = "DL"
    elif slotIdx == params.NumDLSlots: #SpecialSlot
        for sym in range(symbolsPerSlot):
            print(sym)
            numGuard = symbolsPerSlot - params.NumDLSyms - params.NumULSyms
            if sym < params.NumDLSyms:
                slot.loc[sym,'Type'] = 'DL'
            elif sym >= params.NumDLSyms and sym < params.NumDLSyms+numGuard:
                slot.loc[sym,'Type'] = 'G'
            elif sym >= params.NumDLSyms + numGuard:
                slot.loc[sym,'Type'] = 'UL'
            else:
                slot.loc[sym,'Type'] = 'Er'
    else:
        slot['Type'] = "UL"
    return slot

def mergeRBG(df,params,frameIdx,slotIdx):
    print('mergeRBG(df,{},{})'.format(frameIdx,slotIdx))
    a = df[(df['Frame']==frameIdx) & (df['Slot']==slotIdx)]
    # if a.empty: return a
    slot = pd.DataFrame(0,index=np.arange(symbolsPerSlot), columns=np.arange(int(params.NumRBs/2)))
    slot.insert(0,"Frame",frameIdx)
    slot.insert(1,"Slot",slotIdx)
    slot.insert(2,'Type',0)
    slot = slotType(slot,slotIdx,params)
    if a.empty: return slot
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

def mergeAll(df,simParams):
    merged = []
    for i in range(0,df['Frame'].max()):
        for j in range(10):
            data = mergeRBG(df,simParams,i,j)
            if not data.empty:
                merged.append(mergeRBG(df,simParams,i,j))
    df = pd.concat(merged,ignore_index=True)
    print(df)
    return df

def plotSymType(ax,simParams,df):
    xIndex = simParams.NumRBs/2 +0.5
    for i in range(0,len(df.index)):
        ax.annotate(df.loc[i,'Type'][0], (xIndex, (i*-1)-1.05), size=6, ha='right', va='bottom')
    return

def plotSecAxes(ax,simParams,df):

    # -- slotNames
    slotNames = ax.secondary_yaxis(location=0)
    slotLocations = []
    slotNameLabels = []
    spacing= ' '
    for i in range(6,len(df.index),symbolsPerSlot):
        symName = df.loc[i,'Slot']
        slotLocations.append(i*-1)
        slotNameLabels.append('S'+str(symName)+spacing)
    slotNames.set_yticks(slotLocations,labels = slotNameLabels)
    slotNames.tick_params('y', length=0)

    # -- slotLines
    slotLines = ax.secondary_yaxis(location=0)
    slotLinesIdxs = []
    for i in range(0,len(df.index),symbolsPerSlot):
        slotLinesIdxs.append(i*-1)
    slotLines.set_yticks(slotLinesIdxs,labels=[])
    slotLines.tick_params('y', length=10,width=1.5)

    # -- frameNames
    frameNames = ax.secondary_yaxis(location=0)
    frameIdxs = []
    frameNameLabels = []
    frameSpacing = '  '
    for i in range(0,len(df.index),symbolsPerSlot*10):
        frameIdxs.append(i*-1)
        frameNameLabels.append("Frame "+str(df.loc[i,'Frame'])+frameSpacing)
    print(frameIdxs)
    print(frameNameLabels)
    frameNames.set_yticks(frameIdxs,labels=frameNameLabels)
    # frameNames.tick_params('y', length=10,width=1.5)
    # -- frameLines

    return


def plotRBGrid(ax,df):
    print("plotRBGrid()")
    xIndex = 0
    yIndex = -1
    boxWidth = 1
    boxHeight = 1
    RBGRange = len(df.iloc[0])-3
    print("Range:{}".format(RBGRange))
    print(df)
    for rowIdx in range(0,len(df.index)):
        row = df.iloc[rowIdx]
        for i in range(0,RBGRange):
            idxColor = rntiColors[row[i]]
            Pulse = plt.Rectangle((xIndex, yIndex), boxWidth, boxHeight, fill=True,edgecolor='black',facecolor=idxColor) 
            ax.add_patch(Pulse)
            # Index += RadarPW + RadarPRI_s
            xIndex += boxWidth
        yIndex -= boxHeight
        xIndex = 0
    return

def addLegend(ax,simParams,df):
    textSize = 5
    #first legend
    xloc = 0.8
    yloc = 1.005
    ues = []
    for ue in range(1,simParams.NumUEs+1):
        ues.append(patches.Patch(color=rntiColors[ue], label='RNTI:'+str(ue))    )
    ax.add_artist(ax.legend(handles=ues,bbox_to_anchor=(xloc, yloc), loc='lower left',fontsize=textSize))
    

    at2 = AnchoredText("Figure 1(b)",
                       loc='lower left', prop=dict(size=8), frameon=True,
                       bbox_to_anchor=(-0.25, 1.0065),
                       bbox_transform=ax.transAxes
                       )
    ax.add_artist(at2)
    return

def main():
    print("main()")
    #--Import Files
    simParams = simParameters('simParameters.mat')
    df = readSimLogFile('simulationLogs.mat')
    #--Generate df to plot
    # df = mergeAll(df,simParams)

    #--save/load for faster coding interations
    # df.to_pickle('tmp.pkl')
    # df.to_csv('tmp.csv')
    df = pd.read_pickle('tmp.pkl')

    #--setup plot
    fig = plt.figure(figsize=(4,100)) 
    ax = fig.add_subplot(1, 1, 1)
    ax.set_xlim(0,11)
    ax.set_ylim(-1000,0.075) 
    ax.xaxis.set_label_position('top')
    ax.xaxis.tick_top()
    ax.set_yticklabels([])
    #--plot
    plotRBGrid(ax,df)
    plotSymType(ax,simParams,df)
    plotSecAxes(ax,simParams,df)
    addLegend(ax,simParams,df)
    #--adjust
    plt.subplots_adjust(left=0.2, right=.998, top=0.99, bottom=0.001)

    #--save or show
    pltName = simParams.SchedulerStrategy+"_"
    pltName += str(simParams.NumUEs)+"ue_"
    pltName += "TTI"+str(simParams.TTIGranularity)+'_'
    pltName += datetime.now().strftime("%Y%m%d_%H%M%S")
    print(pltName)
    plt.savefig('plt.jpeg')
    # plt.show()
if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()