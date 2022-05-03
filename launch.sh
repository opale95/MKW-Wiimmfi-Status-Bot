#!/bin/bash

timestamp() {
    while IFS= read -r line; do
        printf '%s %s\n' "$(date)" "$line";
    done
}

python3 main.py  |& timestamp >> mkw_wsb.log

