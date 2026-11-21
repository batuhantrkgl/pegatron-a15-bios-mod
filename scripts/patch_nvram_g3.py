#!/usr/bin/env python3
import sys

# Target NVRAM Setup variable records for State After G3 (AFTERG3_EN)
TARGETS = [
    0x220147, 0x220c94, 0x22197a, 0x221ba8, 0x222ad6, 0x222d04,
    0x2239ea, 0x223c18, 0x224a6e, 0x224c9c, 0x225b80, 0x225dae,
    0x226cb4, 0x226ee2, 0x227bc8, 0x227df6, 0x22824e, 0x22847c,
    0x228706, 0x228934, 0x228b70, 0x228d9e, 0x228fda, 0x229208
]

def patch_g3(input_path, output_path):
    with open(input_path, 'rb') as f:
        data = bytearray(f.read())
    
    if len(data) != 4194304:
        raise ValueError(f"Expected 4,194,304 bytes full flash image, got {len(data)}")
    
    count = 0
    for offset in TARGETS:
        if data[offset] == 0x01:
            data[offset] = 0x00
            count += 1
        elif data[offset] == 0x00:
            count += 1
        else:
            print(f"Warning: Unexpected byte at {hex(offset)}: {hex(data[offset])}")
    
    with open(output_path, 'wb') as f:
        f.write(data)
    
    print(f"Updated {count}/{len(TARGETS)} NVRAM records to S0 (auto-power-on). Saved to {output_path}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: patch_nvram_g3.py <input_4mb_image> <output_4mb_image>")
        sys.exit(1)
    patch_g3(sys.argv[1], sys.argv[2])
