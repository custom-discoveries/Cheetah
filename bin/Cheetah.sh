#!/bin/bash
#!/bin/bash
#******************************************************************************
# Copyright (c) 2024, Custom Discoveries Inc.
# All rights reserved.
# Cheetah.sh: Bash shell script to run Cheetah application
# ******************************************************************************
# Determine which system platform we are running on...by resetting CHEETAH_PATH
# ******************************************************************************
export CHEETAH_PATH=""
#******************************************************************************
# Run this script in the bin Directory each time you open a new terminal to set
# the execution path
# ******************************************************************************
# Alternatively, append CHEETAH_PATH in your .bashrc file and append it to the
# PATH variable to make it permanent
# ******************************************************************************
SystemPlatform=`uname`
Machine=`uname -m`
  if [[ $SystemPlatform == "Linux" ]]; then
    echo "Executing Linux Cheetah RAD Tool"
    if [ -z $CHEETAH_PATH ]; then
      CHEETAH_PATH="$(dirname "$(realpath "$0")")/Cheetah-Linux.app"
      echo "Setting CHEETAH_PATH to $CHEETAH_PATH"
      export CHEETAH_PATH
      export PATH=$CHEETAH_PATH:$PATH
    fi
    Cheetah
  elif [[ $SystemPlatform == "Darwin" ]]; then
    echo "Executing Mac Cheetah RAD Tool"
    if [ -z $CHEETAH_PATH ]; then
      if [ $Machine == "x86_64" ]; then
        echo "Setting CHEETAH_PATH for $Machine..."
        CHEETAH_PATH="$(dirname "$(realpath "$0")")/Cheetah-Mac-Intel.app"
        export CHEETAH_PATH
        export PATH=$CHEETAH_PATH:$PATH
      elif [ $Machine == "arm64" ]; then
        echo "Setting CHEETAH_PATH for $Machine..."
        CHEETAH_PATH="$(dirname "$(realpath "$0")")/Cheetah-Mac-Arm64.app"        
        export CHEETAH_PATH
	export PATH=$CHEETAH_PATH:$PATH
      fi
    fi
    Cheetah
  fi
