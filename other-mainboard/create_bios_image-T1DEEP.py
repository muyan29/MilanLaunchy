import os
import logging
import shutil
import hashlib
from typing import Tuple, Optional

# Configure logging format
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def read_file_bytes(filename: str) -> Tuple[bytes, int]:
    if not os.path.exists(filename):
        logging.error(f"File not found: {filename}")
        return b"", 0

    try:
        with open(filename, 'rb') as f:
            content = f.read()
            size = len(content)
            logging.info(f"File read successfully: {filename}, Size: {size} bytes")
            return content, size
    except Exception as e:
        logging.error(f"Error reading file: {e}")
        return b"", 0

def replace_file_content(filename: str, search_bytes: bytes, replace_bytes: bytes) -> None:
    if not os.path.exists(filename):
        logging.error(f"File not found: {filename}")
        return

    try:
        # 1. Read all content
        with open(filename, 'rb') as f:
            content = f.read()

        # 2. Count occurrences
        count = content.count(search_bytes)
        
        if count == 0:
            logging.info(f"No matching content found in '{filename}', no replacement needed.")
            return

        # 3. Perform replacement
        new_content = content.replace(search_bytes, replace_bytes)

        # 4. Write back to file
        with open(filename, 'wb') as f:
            f.write(new_content)

        logging.info(f"File '{filename}' content replacement completed. Replaced {count} occurrence(s).")

    except Exception as e:
        logging.error(f"Error replacing file content: {e}")

def write_at_offset(filename: str, offset: int, data: bytes, write_size: Optional[int] = None) -> None:
    if not os.path.exists(filename):
        logging.error(f"File not found: {filename}")
        return

    try:
        # Determine the actual data to write
        data_to_write = data
        if write_size is not None:
            data_to_write = data[:write_size]
        
        data_len = len(data_to_write)

        with open(filename, 'r+b') as f:
            # Get total file size
            f.seek(0, 2) # Move to end of file
            file_total_size = f.tell()

            # Check if offset is out of bounds
            if offset >= file_total_size:
                logging.warning(f"Offset {offset} exceeds file size {file_total_size}, skipping write.")
                return

            # Core Logic: Ensure overwriting does not increase file size
            # If (offset + data_length) > file_total_size, truncate the data
            if offset + data_len > file_total_size:
                logging.warning("Write data exceeds file end. Truncating data to maintain file size.")
                data_to_write = data_to_write[:file_total_size - offset]
                data_len = len(data_to_write)

            # Move pointer and write
            f.seek(offset)
            f.write(data_to_write)
            
            logging.info(f"Successfully overwrote {data_len} bytes at offset {offset}.")

    except Exception as e:
        logging.error(f"Error writing data: {e}")

def copy_file(src_filename: str, dst_filename: str) -> bool:
    if not os.path.exists(src_filename):
        logging.error(f"Source file not found: {src_filename}")
        return False

    try:
        shutil.copy2(src_filename, dst_filename)
        
        # Verify the file was created
        if os.path.exists(dst_filename):
            src_size = os.path.getsize(src_filename)
            dst_size = os.path.getsize(dst_filename)
            logging.info(f"File copied successfully from '{src_filename}' to '{dst_filename}'. Size: {dst_size} bytes.")
            return True
        else:
            logging.error("Copy operation appeared to finish, but destination file was not found.")
            return False

    except IOError as e:
        logging.error(f"IO Error during file copy: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error during file copy: {e}")
        return False

def create_blank_file(filename: str, size: int) -> bool:
    try:
        with open(filename, 'wb') as f:
            if size > 0:
                # Move the file pointer to the last byte
                f.seek(size - 1)
                # Write a single null byte to define the file boundary
                f.write(b'\x00')
            else:
                # Just open and close to create an empty (0 byte) file
                pass
        
        logging.info(f"Blank file created successfully: {filename}, Size: {size} bytes.")
        return True

    except Exception as e:
        logging.error(f"Error creating blank file: {e}")
        return False

def get_file_md5_bytes(file_name: str) -> bytes:

    md5_hash = hashlib.md5()
    
    with open(file_name, "rb") as f:

        for chunk in iter(lambda: f.read(8192), b""):
            md5_hash.update(chunk)

    return md5_hash.digest()

if __name__ == "__main__":

    # ensure you have "Milan_bl_1008.bin", "Milan_rec_bl_1001.bin", "8036V206.ROM" in this folder, output: "8036V206_MilanLaunchy.ROM"

    # copy "Milan_bl_1008.bin" to "Milan_bl_1008_bp_psb_sev_sig.bin"
    copy_file("Milan_bl_1008.bin", "Milan_bl_1008_bp_psb_sev_sig.bin")


    # this patches the SEV-FW loader check to accept unsigned SEV-FW (with toggle the 0x30 bit in SEV-FW)
    write_at_offset("Milan_bl_1008_bp_psb_sev_sig.bin",0xbf44,bytes.fromhex("00200046"))

    # these patch the PSB check to allow vendor-locked CPU to run on any motherboard
    write_at_offset("Milan_bl_1008_bp_psb_sev_sig.bin",0x116a8,bytes.fromhex("0024"))
    write_at_offset("Milan_bl_1008_bp_psb_sev_sig.bin",0x1177e,bytes.fromhex("0020"))
    write_at_offset("Milan_bl_1008_bp_psb_sev_sig.bin",0x11788,bytes.fromhex("0020"))
    write_at_offset("Milan_bl_1008_bp_psb_sev_sig.bin",0x117a6,bytes.fromhex("0020"))

    #write_at_offset("Milan_bl_1008_bp_psb_sev_sig.bin",0xb9aa,bytes.fromhex("40f2720b"))
    #write_at_offset("Milan_bl_1008_bp_psb_sev_sig.bin",0xb9f6,bytes.fromhex("7226"))
    #write_at_offset("Milan_bl_1008_bp_psb_sev_sig.bin",0xba44,bytes.fromhex("7225"))

    # create a new bootloader image including custom_loader + real(patched)_bootloader
    create_blank_file("Custom_ld_Milan_bl_1008.bin",0x1a000)
    # this header specify load_addr to 0x20000
    header = "0000000000000000000000000000000024505331C0830100000000000000000000000000000000000000000000000000010000000200000094C38E4177D0479292A7AE671D083FB60000000002000000000000000000000000000001000000006E001300FFFF011700000200C0860100000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000AC1B85AE986AA25AA9BBC6655D4FB7E90F66B23906773DC74DECD34BE99426A500000000000000000000000000000000"
    write_at_offset("Custom_ld_Milan_bl_1008.bin",0,bytes.fromhex(header))
    # this loader do memcpy(dst=0,src=0x21000,size=0x18000); and jump to 0x100
    loader = "0F0000EA1F00C0E30030A0E1010053E10500003A4FF07FF5010050E10500003A4FF07FF56FF07FF51EFF2FE13A3F07EE203083E2F4FFFFEA350F07EE200080E2F4FFFFEA34309FE510402DE9212A43E2041093E4001082E5390A53E3FAFFFF1A0619A0E30000A0E3E5FFFFEB4FF07FF56FF07FF5013CA0E303F0A0E1FEFFFFEA10100200"
    write_at_offset("Custom_ld_Milan_bl_1008.bin",0x100,bytes.fromhex(loader))
    # prepare payload to 0x21000
    payload, _ = read_file_bytes("Milan_bl_1008_bp_psb_sev_sig.bin")
    write_at_offset("Custom_ld_Milan_bl_1008.bin",0x1100,payload)

    # create a new BIOS image
    copy_file("T1DEEP0200NMtt.bin", "T1DEEP0200NMtt_MilanLaunchy.ROM")
    # this wpikek result to "b 0x20000"
    new_wpikek = "AA58809B67C0B7FB6559DE25258D74DAFC04578B7300D79EA97ACAC13676BAA0054E3A542CDD6878C35D2315131EEB93"
    write_at_offset("T1DEEP0200NMtt_MilanLaunchy.ROM",0x10a1200,bytes.fromhex(new_wpikek))
    write_at_offset("T1DEEP0200NMtt_MilanLaunchy.ROM",0x1203900,bytes.fromhex(new_wpikek))

    # replace PSP_FW_RECOVERY_BOOT_LOADER
    recbl, _ = read_file_bytes("Milan_rec_bl_1001.bin")
    write_at_offset("T1DEEP0200NMtt_MilanLaunchy.ROM",0x1066900,recbl)
    
    # replace PSP_FW_BOOT_LOADER 
    cus_bl, _ = read_file_bytes("Custom_ld_Milan_bl_1008.bin")
    write_at_offset("T1DEEP0200NMtt_MilanLaunchy.ROM",0x11bf000,cus_bl)

    sevfw, _ = read_file_bytes("sev-1-51-3-original.bin")
    write_at_offset("T1DEEP0200NMtt_MilanLaunchy.ROM",0x12ad800,sevfw)

    md5_bytes = get_file_md5_bytes("T1DEEP0200NMtt_MilanLaunchy.ROM")
    copy_file("T1DEEP0200NM.hpm", "T1DEEP0200NM_MilanLaunchy.hpm")

    ml, _ = read_file_bytes("T1DEEP0200NMtt_MilanLaunchy.ROM")
    write_at_offset("T1DEEP0200NM_MilanLaunchy.hpm",0x55,ml)
    write_at_offset("T1DEEP0200NM_MilanLaunchy.hpm",0x55 + 0x2000000,md5_bytes)