#!/usr/bin/env bash
/usr/bin/chromium-browser \
    --kiosk \
    --noerrdialogs --disable-infobars --disable-session-crashed-bubble \
    --use-fake-ui-for-media-stream \
    http://localhost:8888

