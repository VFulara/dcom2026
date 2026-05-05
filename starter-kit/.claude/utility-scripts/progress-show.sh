#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPORT_FILE="$PROJECT_ROOT/.progress-report.txt"
clear
cat "$REPORT_FILE"
echo
read -n1 -sp "[press any key to close] " _k
