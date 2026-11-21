# Pegatron A15 BIOS modifications

Documentation, patches, and tools for modifying the AMI Aptio IV BIOS on the Pegatron A15 motherboard.

## Overview

The Pegatron A15 motherboard (Intel HM65 chipset) was used in laptops sold under several brand names, most notably the Casper Nirvana A15 series (including A15A, A15FD, and A15HE). The factory BIOS ships with hidden setup menus, no option for automatic power recovery after AC loss, and an outdated boot splash logo.

This repository provides patches, build scripts, and flashing instructions to:
- Enable automatic power-on when AC power connects.
- Expose the Advanced and Chipset submenus on the Main setup page.
- Fix a firmware parser crash that occurs when navigating past the Security tab.
- Replace the default boot splash with the modern Casper vector logo rendered at native BIOS resolution.

## Hardware details

- Motherboard: Pegatron A15
- Platform Controller Hub: Intel HM65 (Cougar Point)
- Flash chip: Macronix MX25L3205D / MX25L3208D (4 MB, SOIC-8)
- BIOS vendor: AMI Aptio IV (UEFI 2.3.1)
- Flash descriptor layout:
  - Flash Descriptor: 0x00000000 - 0x00000FFF (4 KB)
  - Intel ME region: 0x00001000 - 0x001BFFFF (1,788 KB)
  - BIOS region: 0x001C0000 - 0x003FFFFF (2,304 KB / 2,359,296 bytes)

## Technical analysis and modifications

### Auto power on after AC power loss

Intel 6-series chipsets control AC power loss recovery through bit 0 (AFTERG3_EN) of the General Power Management Configuration 3 register (GEN_PMCON_3, PCI D31:F0, offset 0xA4). When set to 1, the platform stays in the S5 soft-off state after AC power is restored. When set to 0, the platform transitions directly to S0 (power on).

Aptio IV stores this setting inside the Setup variable in NVRAM. The target byte is located at offset 0x220c94 in the 4 MB flash dump (offset 0x60c94 inside the BIOS region). Changing this byte from 0x01 to 0x00 across NVRAM records makes the laptop power on immediately whenever AC power is plugged in.

### Setup menu unlock and circular reference crash

Aptio IV stores menu definitions in Human Interface Infrastructure (HII) byte arrays. In module PEGA_Setup (GUID 899407D7-99FE-43D8-9A21-79EC328CAC21), the main form defines reference opcodes (0x0F) that link to submenus:
- Ref: Advanced (Form ID 0x0003)
- Ref: Chipset (Form ID 0x0004)
- Ref: Main (Form ID 0x0002)
- Ref: Boot (Form ID 0x0005)
- Ref: Security (Form ID 0x0007)
- Ref: Save & Exit (Form ID 0x0008)

The OEM image places all six reference opcodes behind a single SuppressIf opcode. Removing the SuppressIf condition wholesale causes the BIOS setup to freeze on a blank blue screen. Form 0x0002 is a duplicate Main page containing its own date and time prompts. When Form 0x0002 is unsuppressed inside the top-level Main form, the AMITSE parser enters infinite recursion.

The fix applies an 88-byte permutation at offset 0x18495 of PEGA_Setup:
1. Place the 11-byte Ref: Advanced and 11-byte Ref: Chipset opcodes directly after the system information fields, outside any SuppressIf block.
2. Keep the SuppressIf opcode directly before Ref: Main, Ref: Boot, Ref: Security, and Ref: Save & Exit.

Because the rearranged opcodes match the exact byte length of the original sequence, file size and relative offsets stay identical.

### Tab navigation crash fix

Unsuppressing Question 0x021F in the Boot form (HII package 3) exposes over seventy raw PCIe root port options. AMITSE allocates a fixed 24-line buffer for setup tabs. Navigating horizontally past the Security tab into Boot triggers a buffer overflow that freezes the interface.

Leaving the Boot and Save & Exit forms in their stock OEM configuration avoids this overflow while keeping full access to Advanced and Chipset via the Main menu.

### Boot splash logo replacement

The boot splash sits in DXE raw section GUID 294B1CEF-9BEB-42D5-9971-0C8963CDAF02. The Aptio IV splash driver requires strict bitmap parameters:
- Dimensions: 400 x 100 pixels
- Color depth: 4 bits per pixel (16 indexed colors)
- Palette: 16-level grayscale palette
- Header: standard 14-byte BMP header followed by 40-byte DIB header (118 bytes total header and palette)
- Compression: none (BI_RGB uncompressed)
- Total file size: exactly 20,118 bytes

The script scripts/convert_logo.py renders the SVG vector to these specifications and outputs the required 4-bit BMP.

## Repository contents

- `assets/casper_logo.bmp`: 400x100 4bpp indexed bitmap boot splash.
- `assets/casper_vector.svg`: source vector graphic.
- `patches/only_main_patch.txt`: UEFIPatch definition for the 88-byte opcode permutation.
- `scripts/convert_logo.py`: generates the 4bpp BMP from an input SVG.
- `scripts/patch_nvram_g3.py`: sets AFTERG3_EN to 0 across NVRAM records.
- `scripts/assemble_rom.py`: inserts a 2,359,296-byte BIOS payload into a 4 MB SPI image.
- `scripts/flash_bios.sh`: flashes and verifies the BIOS region using flashrom.
- `layout.txt`: flashrom layout targeting the BIOS region (001c0000:003fffff).

## Flashing guide

### Requirements

- A Linux environment running on the target machine with root privileges.
- flashrom installed.
- python3 for verification scripts.

### 1. Read and backup the current SPI flash

Read the chip twice and verify that the two dumps are identical:
```bash
flashrom -p internal -c "MX25L3205D/MX25L3208D" -r backup1.bin
flashrom -p internal -c "MX25L3205D/MX25L3208D" -r backup2.bin
cmp backup1.bin backup2.bin
```

Keep `backup1.bin` in a safe location outside the machine.

### 2. Flash the modified image

Use the provided flash script. The script uses `layout.txt` to restrict writes to the BIOS region (`0x001C0000 - 0x003FFFFF`), leaving the Intel Management Engine and Flash Descriptor untouched:
```bash
sudo ./scripts/flash_bios.sh bios_region_dump_casper_logo.bin
```

The script automatically verifies the written region against the source image after writing.

### Hardware recovery

If the machine fails to boot due to an interrupted write:
1. Disconnect the AC adapter, main battery, and CMOS battery.
2. Connect an external programmer (such as a CH341A or Raspberry Pi) to the SOIC-8 flash chip using a test clip.
3. Write the 4 MB backup dump:
```bash
flashrom -p ch341a_spi -c "MX25L3205D/MX25L3208D" -w backup1.bin
```

## Prebuilt binaries

Prebuilt ROM files and payloads are available on the Releases page:
- `bios_region_dump_casper_logo.bin`: full 4 MB image with auto-power-on, unlocked menus, and modern Casper logo.
- `bios_region_dump_stable_unlocked.bin`: full 4 MB image with auto-power-on, unlocked menus, and default AMI logo.
- `payload_casper_logo.bin`: 2.25 MB BIOS payload with modern Casper logo.
- `payload_only_main.bin`: 2.25 MB BIOS payload with default AMI logo.
