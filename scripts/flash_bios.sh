#!/usr/bin/env bash
set -euo pipefail

CHIP="MX25L3205D/MX25L3208D"
LAYOUT_FILE="$(dirname "$0")/../layout.txt"

if [ $# -lt 1 ]; then
    echo "Usage: $0 <path-to-bios-rom-or-payload>"
    exit 1
fi

INPUT_FILE="$1"

if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: File $INPUT_FILE not found"
    exit 1
fi

FILE_SIZE=$(stat -c%s "$INPUT_FILE")

if [ "$FILE_SIZE" -eq 4194304 ]; then
    IMAGE_TO_FLASH="$INPUT_FILE"
elif [ "$FILE_SIZE" -eq 2359296 ]; then
    echo "Input is a 2.25MB BIOS-region payload. Creating temporary 4MB flash image..."
    IMAGE_TO_FLASH="/tmp/flash_temp_4mb.bin"
    flashrom -p internal -c "$CHIP" -r /tmp/current_dump.bin
    cp /tmp/current_dump.bin "$IMAGE_TO_FLASH"
    python3 -c '
with open("/tmp/flash_temp_4mb.bin", "r+b") as f:
    payload = open("'$INPUT_FILE'", "rb").read()
    f.seek(0x1c0000)
    f.write(payload)
'
else
    echo "Error: Invalid file size $FILE_SIZE. Expected 4,194,304 or 2,359,296 bytes."
    exit 1
fi

echo "Writing BIOS region to SPI flash..."
flashrom -p internal -c "$CHIP" -l "$LAYOUT_FILE" -i bios --noverify-all -w "$IMAGE_TO_FLASH"

echo "Verifying BIOS region readback..."
flashrom -p internal -c "$CHIP" -l "$LAYOUT_FILE" -i bios -r /tmp/verify_readback.bin
python3 -c '
orig = open("'$IMAGE_TO_FLASH'", "rb").read()[0x1c0000:0x400000]
readback = open("/tmp/verify_readback.bin", "rb").read()[0x1c0000:0x400000]
if orig == readback:
    print("Verification successful: 100% bit-for-bit match.")
else:
    print("Error: Verification mismatch between flashed image and readback.")
    exit(1)
'
