#!/bin/bash
if systemctl --user is-active gammastep.service >/dev/null 2>&1; then
    systemctl --user stop gammastep.service
    notify-send -u low -t 2000 "Night Light" "Đã tắt Chế độ ban đêm"
else
    # Ensure geoclue agent is running
    if ! pgrep -f "geoclue-2.0/demos/agent" >/dev/null; then
        /usr/libexec/geoclue-2.0/demos/agent &
    fi
    systemctl --user start gammastep.service
    notify-send -u low -t 2000 "Night Light" "Đã bật Chế độ ban đêm"
fi
