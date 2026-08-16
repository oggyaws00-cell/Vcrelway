#!/bin/bash
echo "Compiling OGGY binary..."
gcc -pthread -o oggy oggy_destroyer.c

if [ -f "./oggy" ]; then
    echo "Compilation successful. Starting bot..."
    python3 bot.py
else
    echo "Compilation failed! Exiting."
    exit 1
fi
