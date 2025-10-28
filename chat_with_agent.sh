#!/bin/bash
# Simple wrapper to chat with your Claude Agent
# Usage: ./chat_with_agent.sh "Your message here"

cd "$(dirname "$0")"
./venv/bin/python test_airflow_agent_main.py "$@"
