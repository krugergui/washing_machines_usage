#!/bin/bash
parent_path=$( cd "$(dirname "${BASH_SOURCE[1]}")" ; pwd -P )

current_time=$(date "+%Y%m%d-%H%M%S")
devices=$(adb devices | awk '{print $1}' | tail -n +2)

for device in $devices
do
    adb -s $device exec-out screencap -p > "`dirname $0`"/../../screenshots/landing_area/screenshot_${device}_${current_time}.png
done
