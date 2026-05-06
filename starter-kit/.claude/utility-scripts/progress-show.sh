#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPORT_FILE="$PROJECT_ROOT/.progress-report.txt"

while true; do
	clear
	if [[ -f "$REPORT_FILE" ]]; then
		cat "$REPORT_FILE"
	else
		echo "Progress report file not found: $REPORT_FILE"
	fi
	echo
	echo "[auto-refresh: 1s] Press q to close"

	# Wait up to 1 second for input; refresh if no key was pressed.
	if read -r -s -n1 -t 1 _k; then
		if [[ "$_k" == "q" || "$_k" == "Q" ]]; then
			break
		fi
	fi
done
