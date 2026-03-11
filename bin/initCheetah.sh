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
# #echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc
# ******************************************************************************
SystemPlatform=`uname`
Machine=`uname -m`
  if [[ $SystemPlatform == "Linux" ]]; then
    echo "Executing Linux Cheetah RAD Tool"
    if [ -z $CHEETAH_PATH ]; then
      CHEETAH_PATH="$(cd "$(dirname -- "$0")" && pwd)/Cheetah-Linux.app"
      echo "Setting CHEETAH_PATH to $CHEETAH_PATH"
      echo "export PATH=\"\$PATH:$CHEETAH_PATH\"" >> ~/.bashrc && source ~/.bashrc
    fi
  elif [[ $SystemPlatform == "Darwin" ]]; then
    echo "Executing Mac Cheetah RAD Tool"
    if [ -z $CHEETAH_PATH ]; then
      if [ $Machine == "x86_64" ]; then
        echo "Setting CHEETAH_PATH for $Machine..."
        CHEETAH_PATH="$(cd "$(dirname -- "$0")" && pwd)/Cheetah-Mac-Intel.app"
        echo "Setting CHEETAH_PATH to $CHEETAH_PATH"
      elif [ $Machine == "arm64" ]; then
        echo "Setting CHEETAH_PATH for $Machine..."
        CHEETAH_PATH="$(cd "$(dirname  -- "$0")" && pwd)/Cheetah-Mac-Arm64.app"
        echo "Setting CHEETAH_PATH to $CHEETAH_PATH"
      fi
      echo "export PATH=\"\$PATH:$CHEETAH_PATH\"" >> ~/.bashrc && source ~/.bashrc
    fi
  fi
