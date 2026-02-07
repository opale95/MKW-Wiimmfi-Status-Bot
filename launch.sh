#!/bin/bash

timestamp() {
    while IFS= read -r line; do
        printf '%s %s\n' "$(date)" "$line";
    done
}

source "venv/bin/activate"
python main.py  |& timestamp >> mkw_wsb.log

