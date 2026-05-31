#!/bin/bash

############################
# See README.md
############################

if ! pandoc -v 2>&1 >/dev/null; then
    echo "Please install the pandoc package."
    exit 1
fi

# generate the md file from the source csv file
echo "Processing csv file to generate .md file for input to other tools"
python3 csv-to-md.py

# generate the plain text table [api-doc.txt](api-doc.txt).
echo "Generating the plain text table ..."
python3 md-to-doc.py api-doc.md > api-doc.txt

# generate the OpenAPI specification [hamclock-openapi.yaml](hamclock-openapi.yaml).
echo "Generating the OpenAPI specification ..."
python3 md-to-openapi.py api-doc.md hamclock-openapi.yaml

# generate the interactive HTML documentation [hamclock-api-docs.html](hamclock-api-docs.html).
echo "Generating the interactive OpenAPI HTML documentation ..."
python3 openapi-to-html.py

# convert MarkDown to HTML via pandoc then inject enum definitions and hyperlinks
echo "Converting MarkDown to HTML ..."

# Wrap api-doc.css in <style> tags so pandoc -H embeds it correctly
STYLE_HEADER=$(mktemp /tmp/api-doc-header-XXXX.html)
echo "<style>" > "$STYLE_HEADER"
cat api-doc.css >> "$STYLE_HEADER"
echo "</style>" >> "$STYLE_HEADER"

pandoc api-doc.md -so api-doc-raw.html \
    --metadata title="HamClock API Documentation" \
    -H "$STYLE_HEADER"

rm -f "$STYLE_HEADER"

python3 post-process.py api-doc-raw.html api-doc.md api-doc.html
rm -f api-doc-raw.html
