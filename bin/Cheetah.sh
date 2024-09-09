#!/bin/bash
#******************************************************************************
# Copyright (c) 2024, Custom Discoveries Inc.
# All rights reserved.
# Cheetah.sh: Bash shell script to run Cheetah application
#******************************************************************************
# Run this script in the bin Directory each time you open a new terminal to set
# the execution path
# ******************************************************************************
# Alternatively, set CHEETAH_PATH in your bashrc file and append it to the PATH
# variable to make it permanent
# ******************************************************************************

# ******************************************************************************
# Determine which system platform we are running on...
# ******************************************************************************
SystemPlatform=`uname`
  if [[ $SystemPlatform == "Linux" ]]; then
    echo "Executing Linux Cheetah RAD Tool"
    if [ -z $CHEETAH_PATH ]; then
      echo "Setting CHEETAH_PATH..."
      CHEETAH_PATH=`pwd`/Cheetah-Linux.app
      export CHEETAH_PATH
      export PATH=$PATH:$CHEETAH_PATH
    fi    
  elif [[ $SystemPlatform == "Darwin" ]]; then
    echo "Executing Mac Cheetah RAD Tool"
    if [ -z $CHEETAH_PATH ]; then
      echo "Setting CHEETAH_PATH..."
      CHEETAH_PATH=`pwd`/Cheetah-Mac.app
      export CHEETAH_PATH
      export PATH=$PATH:$CHEETAH_PATH
    fi
  fi
Cheetah
