#!/bin/bash
pandoc _meta/metadata.yaml Chapter_*.md --toc --toc-depth=2 --css=_meta/style.css -o novel.epub

