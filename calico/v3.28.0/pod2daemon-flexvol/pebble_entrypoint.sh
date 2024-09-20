#!/bin/bash

echo "invocation: $0 $@"

# Required to prevent Pebble from considering the service to have
# exited too quickly to be worth restarting or respecting the
# "on-failure: shutdown" directive and thus hanging indefinitely:
# https://github.com/canonical/pebble/issues/240#issuecomment-1599722443
sleep 1.1

/usr/local/bin/flexvol.sh "$@"
