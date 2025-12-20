#!/bin/bash

# Check if argument is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <ExtractFromBookFolder>"
  exit 1
fi

BOOK_DIR="$1"

# Run pandoc
pandoc _meta/metadata.yaml "$BOOK_DIR"/Translations/Chapter_*.md \
  --toc --toc-depth=2 --css=_meta/style.css \
  -o "$BOOK_DIR".epub

