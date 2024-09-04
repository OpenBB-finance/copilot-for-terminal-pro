#!/bin/bash

set -e

uvicorn findb_copilot.main:app --loop uvloop --proxy-headers --host 0.0.0.0 --port 7777 --workers 4 $1

