#!/usr/bin/env python3
import sys

def assemble(base_4mb_path, payload_path, output_path):
    with open(base_4mb_path, 'rb') as f:
        base = bytearray(f.read())
    with open(payload_path, 'rb') as f:
        payload = f.read()
    
    if len(base) != 4194304:
        raise ValueError(f"Base image size must be 4,194,304 bytes, got {len(base)}")
    if len(payload) != 2359296:
        raise ValueError(f"BIOS payload size must be 2,359,296 bytes, got {len(payload)}")
    
    # Insert payload at BIOS region offset 0x1c0000
    base[0x1c0000:0x1c0000 + len(payload)] = payload
    
    with open(output_path, 'wb') as f:
        f.write(base)
    
    print(f"Assembled 4MB image successfully to {output_path}")
    print(f"NVRAM State After G3 at 0x220c94: {hex(base[0x220c94])}")

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: assemble_rom.py <base_4mb_image> <payload_2.25mb> <output_4mb_image>")
        sys.exit(1)
    assemble(sys.argv[1], sys.argv[2], sys.argv[3])
