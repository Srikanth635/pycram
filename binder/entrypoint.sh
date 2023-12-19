#!/bin/bash

source ${PYCRAM_WS}/devel/setup.bash
roslaunch rvizweb rvizweb.launch config_file:=/binder/rvizweb-config.json &

jupyter lab workspaces import ${PYCRAM_WS}/src/pycram/binder/workspace.json

# Use xvfb virtual display when there is no display connected.
if [ -n "$DISPLAY" ]; then
  exec "$@"
else
  xvfb-run exec "$@"
fi