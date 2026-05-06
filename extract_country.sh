#!/bin/bash

if [ -z "$1" ]; then
    echo "ERROR: Country code not provided."
    echo "USAGE: ./extract_country.sh <COUNTRY_CODE> [INPUT_FILE]"
    echo "EXAMPLE: ./extract_country.sh PL"
    exit 1
fi

COUNTRY_CODE=$1
INPUT_FILE=${2:-"ESTAT_Census_2021_V2.csv"}
OUTPUT_FILE="${COUNTRY_CODE}_population.csv"
SEARCH_PATTERN="${COUNTRY_CODE}_"

if [ ! -f "$INPUT_FILE" ]; then
    echo "ERROR: File '$INPUT_FILE' not found."
    exit 1
fi

echo "Processing file: $INPUT_FILE"
echo "Searching for country: $COUNTRY_CODE (pattern: '$SEARCH_PATTERN')"

head -n 1 "$INPUT_FILE" > "$OUTPUT_FILE"
grep "$SEARCH_PATTERN" "$INPUT_FILE" >> "$OUTPUT_FILE"

LINES=$(wc -l < "$OUTPUT_FILE")

if [ "$LINES" -le 1 ]; then
    echo "WARNING: No records found for country code '$COUNTRY_CODE'."
    rm "$OUTPUT_FILE"
else
    RECORDS=$((LINES - 1))
    echo "SUCCESS: Saved $RECORDS populated grids to $OUTPUT_FILE"
fi