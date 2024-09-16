#!/usr/bin/env bash

echo "folderRun.sh"
echo $#
echo $1

for folder in $1/*/; do 
    echo $folder
    for file in $folder*.*; do 
        echo $file
        if [[ $file == *"simParameters"* ]]; then
        par=$file;
        fi
        if [[ $file == *"simulationMetrics"* ]]; then
        met=$file;
        fi
    done
    ./ScheduleVisulizer.py $par $met $folder
done
