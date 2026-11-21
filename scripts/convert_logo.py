#!/usr/bin/env python3
import sys
import struct
import subprocess
from PIL import Image

def svg_to_bmp(svg_path, output_bmp_path):
    # Read SVG and ensure fill is white
    with open(svg_path, 'r', encoding='utf-8') as f:
        svg_data = f.read()
    
    # Replace any blue/black fills with pure white
    svg_white = svg_data.replace('#0b1f8f', '#ffffff').replace('#000000', '#ffffff')
    tmp_svg = '/tmp/logo_white_tmp.svg'
    tmp_png = '/tmp/logo_render_tmp.png'
    
    with open(tmp_svg, 'w', encoding='utf-8') as f:
        f.write(svg_white)
    
    # Render with rsvg-convert to height 56 (width ~182 for Casper aspect ratio)
    subprocess.run(['rsvg-convert', '-h', '56', tmp_svg, '-o', tmp_png], check=True)
    
    logo = Image.open(tmp_png)
    canvas = Image.new('L', (400, 100), color=0)
    
    x_pos = (400 - logo.width) // 2
    y_pos = (100 - logo.height) // 2
    
    if 'A' in logo.getbands():
        mask = logo.split()[-1]
        canvas.paste(logo.convert('L'), (x_pos, y_pos), mask=mask)
    else:
        canvas.paste(logo.convert('L'), (x_pos, y_pos))
    
    # Build 16-color grayscale palette (4-bit indexed)
    palette_bytes = bytearray()
    for i in range(16):
        val = int(round(i * 255.0 / 15.0))
        palette_bytes += struct.pack('BBBB', val, val, val, 0)
    
    width, height = 400, 100
    file_size = 54 + len(palette_bytes) + (width // 2) * height
    offset_data = 54 + len(palette_bytes)
    
    bmp_header = struct.pack('<2sIHHI', b'BM', file_size, 0, 0, offset_data)
    dib_header = struct.pack('<IIIHHIIIIII',
        40, width, height, 1, 4, 0, (width // 2) * height, 0, 0, 16, 16
    )
    
    pixel_data = bytearray()
    for y in range(height - 1, -1, -1):
        row_bytes = bytearray()
        for x in range(0, width, 2):
            p1 = canvas.getpixel((x, y))
            p2 = canvas.getpixel((x + 1, y))
            idx1 = min(15, max(0, int(round(p1 * 15.0 / 255.0))))
            idx2 = min(15, max(0, int(round(p2 * 15.0 / 255.0))))
            row_bytes.append((idx1 << 4) | idx2)
        pixel_data += row_bytes
    
    final_bmp = bmp_header + dib_header + bytes(palette_bytes) + bytes(pixel_data)
    with open(output_bmp_path, 'wb') as f:
        f.write(final_bmp)
    print(f'Successfully generated {output_bmp_path} ({len(final_bmp)} bytes)')

if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else '/root/pegatron-a15-bios-mod/assets/casper_vector.svg'
    dst = sys.argv[2] if len(sys.argv) > 2 else '/tmp/test_casper.bmp'
    svg_to_bmp(src, dst)
