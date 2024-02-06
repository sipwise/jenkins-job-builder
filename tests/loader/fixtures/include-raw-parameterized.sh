#!/bin/bash
#
# sample script to check that variables are expanded
# when using the !include-raw-expand: application yaml tag

VAR1="{num}"
VAR2="world"
VAR3="${{VAR1}} ${{VAR2}}"

[[ -n "${{VAR3}}" ]] && {{
    # this next section is executed as one
    echo "${{VAR3}}"
    exit 0
}}
