#!/bin/bash
# Setup weekly launchd job for TC Ads QA reports
# Runs every Monday at 7:00 AM AEST

PLIST_NAME="com.trilogycare.ads-qa-weekly"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_NAME}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>${SCRIPT_DIR}/weekly_report.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${SCRIPT_DIR}</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>1</integer>
        <key>Hour</key>
        <integer>7</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>${SCRIPT_DIR}/reports/weekly_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>${SCRIPT_DIR}/reports/weekly_stderr.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
EOF

echo "Created launchd plist at: $PLIST_PATH"

# Load the job
launchctl unload "$PLIST_PATH" 2>/dev/null
launchctl load "$PLIST_PATH"
echo "Loaded weekly schedule: Every Monday at 7:00 AM"
echo ""
echo "To check status:  launchctl list | grep ads-qa"
echo "To unload:        launchctl unload '$PLIST_PATH'"
echo "To run manually:  python3 ${SCRIPT_DIR}/weekly_report.py"
