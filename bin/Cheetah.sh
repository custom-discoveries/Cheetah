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
if [ -z $CHEETAH_PATH ]; then
  echo "Setting CHEETAH_PATH..."
  CHEETAH_PATH=`pwd`
  export CHEETAH_PATH
  export PATH=$PATH:$CHEETAH_PATH
fi
# ******************************************************************************
# Determine which system platform we are running on...
# ******************************************************************************
SystemPlatform=`uname`
  if [[ $SystemPlatform == "Linux" ]]; then
    echo "Executing Linux Cheetah RAD Tool"
      $CHEETAH_PATH/Cheetah-Linux.app/Cheetah
  elif [[ $SystemPlatform == "Darwin" ]]; then
    echo "Executing Mac Cheetah RAD Tool"
      $CHEETAH_PATH/Cheetah-Mac.app/Cheetah
  fi
