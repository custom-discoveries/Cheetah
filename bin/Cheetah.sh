#!/bin/bash
#******************************************************************************
# Copyright (c) 2024, Custom Discoveries Inc.
# All rights reserved.
# Cheetah.sh: Bash shell script to run Cheetah application
# ******************************************************************************
# Determine which system platform we are running on...
# ******************************************************************************

#******************************************************************************
# Run this script in the bin Directory each time you open a new terminal to set
# the execution path
# ******************************************************************************
# Alternatively, set CHEETAH_PATH in your bashrc file and append it to the PATH
# variable to make it permanent
# ******************************************************************************
SystemPlatform=`uname`
Machine=`uname -m`
  if [[ $SystemPlatform == "Linux" ]]; then
    echo "Executing Linux Cheetah RAD Tool"
    if [ -z $CHEETAH_PATH ]; then
      echo "Setting CHEETAH_PATH..."
      CHEETAH_PATH=`pwd`/Cheetah-Linux.app
      export CHEETAH_PATH
      export PATH=$PATH:$CHEETAH_PATH
    fi
    Cheetah
  elif [[ $SystemPlatform == "Darwin" ]]; then
    echo "Executing Mac Cheetah RAD Tool"
    if [ -z $CHEETAH_PATH ]; then
      if [ $Machine == "x86_64" ]; then
        echo "Setting CHEETAH_PATH for $Machine..."
        CHEETAH_PATH=`pwd`/Cheetah-Mac-Intel.app
        export CHEETAH_PATH
        export PATH=$PATH:$CHEETAH_PATH
      elif [ $Machine == "arm64" ]; then
        echo "Setting CHEETAH_PATH for $Machine..."
        CHEETAH_PATH=`pwd`/Cheetah-Mac-Arm64.app
        export CHEETAH_PATH
        export PATH=$PATH:$CHEETAH_PATH
      fi
    fi
    Cheetah
  fi
