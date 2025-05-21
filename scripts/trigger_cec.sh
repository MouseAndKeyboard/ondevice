#!/usr/bin/env bash
#
# Trigger-CEC helper for Raspberry Pi
#  - CEC adapter      : /dev/cec1
#  - Pi  logical addr : 1 (Playback Device)
#  - TV  logical addr : 0

CEC_DEV=/dev/cec1
PI_ADDR=1          # transmitter          (source)
TV_ADDR=0          # destination / display

# Convenience wrapper – sends one line of CEC shell syntax
cec_send() {
  echo "$1" | cec-client "$CEC_DEV" -s -d 1 >/dev/null
}

############ Actions you might want when a call arrives ############

# 1. Power-on the TV (if it’s in standby)
cec_send "on $TV_ADDR"

# 2. Tell the TV to switch to, and display, the Pi’s HDMI input
cec_send "as"                    # “active source”
#   – equivalent raw TX form (for reference):  'tx 1F:82:10:00'

# 3. (Optional) Set OSD text so the TV shows a friendly label
cec_send "tx ${PI_ADDR}0:46:49:6E:63:6F:6D:69:6E:67"  # "Incoming" in ASCII

####################################################################
# Add any other CEC commands your TV understands here
####################################################################

