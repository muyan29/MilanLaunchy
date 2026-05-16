# MilanLaunchy Firmware Loader

## Overview

MilanLaunchy exploits known vulnerabilities to allow the execution of arbitrary unsigned ASP bootloaders, SEV-SNP firmware, and other system components on the AMD EPYC 7003 series (codenamed "Milan") and Threadripper PRO 59x5WX processors (codenamed "Chagall"). MilanLaunchy does not require physical access to the target machine; it can be executed solely by flashing the BIOS firmware, which can be performed via the USB/BMC/SPI-Flash-Programmer.

It is worth noting that MilanLaunchy enables you to load an off-chip bootloader just like loading a legitimate off-chip bootloader, which allows you to hook desired functions while ensuring a successful boot into the x86 system.

## Feature Highlights

### Execute Customized/modified Bootloader/SMU/SEV-SNP/SecureOS Firmware

The AMD Secure Processor (ASP) (also known as Platform Security Processor (PSP)) functions as the integrated hardware root of trust within the AMD CPU, responsible for initializing the platform and enforcing the security integrity of the entire platform. For security researchers: You can now execute arbitrary, unsigned custom firmware, granting you full access to explore the inner workings of the ASP.

### Bypass Platform Secure Boot (PSB)  on Vendor-locked CPUs

AMD's PSB includes a feature known as vendor-locking, which allows OEMs to restrict AMD CPUs to run exclusively on motherboards manufactured by them. This restriction is enforced by irreversibly blowing fuses within the CPU to permanently record a specific vendor ID or public key hash. During the boot sequence, the ASP off-chip bootloader validates these fuses against the platform; if the check fails, the CPU refuses to boot.

With MilanLaunchy you can patch the firmware to bypass these checks, allowing vendor-locked Milan or Chagall processors to run on any compatible motherboard just like unlocked ones.

## Before Deploying

Please read [this paper](https://arxiv.org/abs/2605.12990) to understand how MilanLaunchy works, its impact, and our responsible disclosure.

**Risks:**

Before using MilanLaunchy, you should fully understand the risks and know how to recover from a failed boot, especially if you attempt to use MilanLaunchy on other motherboards. You must have access to (and know how to use) a BMC or a hardware SPI-Flash programmer to restore the original firmware if the system fails to boot. Do not attempt to use this tool unless you are proficient in recovering a system from a failed flash. The author assumes no responsibility or liability for any damage, data loss, or system instability caused by the use of MilanLaunchy.

**Determine the BIOS flashing methods supported by your motherboard**

The files used when flashing the SPI-Flash via USB/UEFI Shell, BMC, or an SPI-Flash programmer are sometimes different. Please familiarize yourself with the flashing methods supported by your motherboard manufacturer.

For a small number of motherboards, the BMC may prevent you from flashing a modified BIOS image. If this is enforced via checksums, please manually correct the relevant structures, just as we did in `other-mainboard`. If it still does not work, you can try using an SPI-Flash programmer; this method will always be viable.

## Deploying MilanLaunchy on Tyan S8036

Taking the Tyan S8036 as an example, the files used for flashing via BMC and UEFI Shell are identical for this motherboard, making it very convenient.

Please refer to the `create_bios_image.py` script we have provided. The script contains the core components required to build a MilanLaunchy image based on version "8036V206", and already integrates the hooks to bypass PSB and allow loading arbitrary SEV-SNP firmware. Due to copyright restrictions, we do not directly provide the original BIOS images and firmware; you can download them from the OEM's official [website](https://www.mitaccomputing.com/en/downloads/Motherboards/S8036_S8036GM2NE#dw) and extract the required files using [psptool](https://github.com/pspreverse/psptool).

## Deploying MilanLaunchy on Other Motherboards

You will need to use [psptool](https://github.com/pspreverse/psptool) to analyze the offset locations of the corresponding firmware, and then modify the corresponding offsets in the script. For some motherboards (such as Threadripper PRO series motherboards), you may need to manually reverse engineer them. Below are the relevant scripts for deploying MilanLaunchy on two other motherboards for reference. Among them, the T1DEEP is an EPYC motherboard, and the MC62G40 is a WRX80 (Threadripper PRO 59x5WX) motherboard.

If you have any issues while reproducing MilanLaunchy, feel free to contact me.

## Contact Me

Muyan Shen

Email: cwindy2024@outlook.com

