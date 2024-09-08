#!/bin/bash
SystemPlatform=`uname`
  if [[ $SystemPlatform == "Linux" ]]; then
    echo "Executing Linux Cheetah RAD Tool"
      ./Cheetah-Linux.app/Cheetah
  elif [[ $SystemPlatform == "Darwin" ]]; then
    echo "Executing Mac Cheetah RAD Tool"
    ./Cheetah-Mac.app/Cheetah
  fi
