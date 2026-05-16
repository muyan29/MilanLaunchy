import os
import logging
import shutil
from typing import Tuple, Optional
import struct

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

def fletcher32(data):
    """
    Calculate the standard Fletcher-32 checksum.
    Processes data in 16-bit blocks and returns a 32-bit result.
    """
    # Pad with a zero byte if the data length is odd to align to 16-bit
    if len(data) % 2 != 0:
        data += b'\x00'
    
    sum1 = 0
    sum2 = 0
    
    # Iterate over data in 16-bit (2-byte) steps
    for i in range(0, len(data), 2):
        # Read 16-bit data as Little-Endian "<H" by default.
        # Change to ">H" if your target system uses Big-Endian.
        word = struct.unpack_from("<H", data, i)[0]
        
        sum1 = (sum1 + word) % 65535
        sum2 = (sum2 + sum1) % 65535
        
    return (sum2 << 16) | sum1

def verify_and_update_checksum(file_path, checksum_offset, data_start, data_end):
    # Define offsets and range based on your requirements
    #checksum_offset = 0x16C0004
    #data_start = 0x16C0008 # remember to bump if add wp_ikek...
    #data_end = 0x16C01D0
    data_size = data_end - data_start
    
    if not os.path.exists(file_path):
        print(f"[-] Error: File '{file_path}' not found.")
        return

    with open(file_path, 'r+b') as f:
        # 1. Read the original checksum (4 bytes)
        f.seek(checksum_offset)
        # Read as a 32-bit unsigned integer in Little-Endian "<I"
        stored_checksum = struct.unpack("<I", f.read(4))[0]
        
        # 2. Read the data block to be checksummed
        f.seek(data_start)
        data = f.read(data_size)
        
        if len(data) != data_size:
            print(f"[-] Error: Cannot read the full data block. Expected {data_size} bytes, got {len(data)} bytes.")
            return
            
        # 3. Calculate Fletcher-32
        calculated_checksum = fletcher32(data)
        
        print(f"[*] Target data range: 0x{data_start:X} - 0x{data_end:X} ({data_size} bytes)")
        print(f"[*] Stored checksum in file: 0x{stored_checksum:08X}")
        print(f"[*] Calculated checksum:     0x{calculated_checksum:08X}")
        
        # 4. Compare and update
        if stored_checksum == calculated_checksum:
            print("[+] Checksums match. No modifications needed.")
        else:
            print("[-] Checksum mismatch! Updating the checksum in the file...")
            f.seek(checksum_offset)
            # Write the newly calculated checksum back to the file in Little-Endian
            f.write(struct.pack("<I", calculated_checksum))
            print("[+] Update complete.")

def calculate_checksum16_big_endian(filename, size_limit=0x02000000):
    """
    Calculates the 16-bit checksum (simple byte accumulation) of a file.
    
    Args:
        filename (str): The path to the firmware file.
        size_limit (int): The maximum number of bytes to read (default is 32MB).
                          This prevents reading the appended signature/footer.
                          
    Returns:
        bytes: A 2-byte object representing the 16-bit checksum in Big-Endian format.
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File not found: {filename}")

    total_sum = 0
    bytes_read = 0
    chunk_size = 65536  # Read in 64KB chunks for memory efficiency

    with open(filename, 'rb') as f:
        while bytes_read < size_limit:
            # Calculate how many bytes to read in the current iteration
            read_size = min(chunk_size, size_limit - bytes_read)
            chunk = f.read(read_size)
            
            if not chunk:
                break  # Reached End Of File (EOF)
            
            # Accumulate the value of each byte in the current chunk
            total_sum += sum(chunk)
            bytes_read += len(chunk)

    # Keep only the lower 16 bits of the accumulated sum
    checksum16 = total_sum & 0xFFFF

    # Convert the integer to a 2-byte object in Big-Endian order
    return checksum16.to_bytes(2, byteorder='big')

if __name__ == "__main__":

    # ensure you have "Milan_bl_1008.bin", "Milan_rec_bl_1001.bin", "8036V206.ROM" in this folder, output: "8036V206_MilanLaunchy.ROM"

    # copy "Milan_bl_1008.bin" to "Milan_bl_1008_bp_psb_sev_sig.bin"
    copy_file("chagallbl_260027.bin", "chagallbl_260027_bp_psb.bin")

    # these patch the PSB check to allow vendor-locked CPU to run on any motherboard
    write_at_offset("chagallbl_260027_bp_psb.bin",0xd1b2,bytes.fromhex("0024")) # CHECK: 0xd1b2,mov r4,r0-->mov r4,0
    write_at_offset("chagallbl_260027_bp_psb.bin",0x899e,bytes.fromhex("0020")) # CHECK: 0x899e mov r0,r4-->mov r0,0
    write_at_offset("chagallbl_260027_bp_psb.bin",0xd1ec,bytes.fromhex("0024"))
    write_at_offset("chagallbl_260027_bp_psb.bin",0xd1a4,bytes.fromhex("0024"))
    write_at_offset("chagallbl_260027_bp_psb.bin",0xd218,bytes.fromhex("00200020")) 
    write_at_offset("chagallbl_260027_bp_psb.bin",0x68e6,bytes.fromhex("0020")) 
    #write_at_offset("Milan_bl_1008_bp_psb_sev_sig.bin",0x31d0,bytes.fromhex("00200046"))

    # create a new bootloader image including custom_loader + real(patched)_bootloader
    create_blank_file("Custom_ld_chagallbl_260027.bin",0x1a000)
    # this header specify load_addr to 0x20000
    header = "0000000000000000000000000000000024505331C0830100000000000000000000000000000000000000000000000000010000000200000094C38E4177D0479292A7AE671D083FB60000000002000000000000000000000000000001000000006E001300FFFF011700000200C0860100000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000AC1B85AE986AA25AA9BBC6655D4FB7E90F66B23906773DC74DECD34BE99426A500000000000000000000000000000000"
    write_at_offset("Custom_ld_chagallbl_260027.bin",0,bytes.fromhex(header))
    # this loader do memcpy(dst=0,src=0x21000,size=0x18000); and jump to 0x100
    loader = "0F0000EA1F00C0E30030A0E1010053E10500003A4FF07FF5010050E10500003A4FF07FF56FF07FF51EFF2FE13A3F07EE203083E2F4FFFFEA350F07EE200080E2F4FFFFEA34309FE510402DE9212A43E2041093E4001082E5390A53E3FAFFFF1A0619A0E30000A0E3E5FFFFEB4FF07FF56FF07FF5013CA0E303F0A0E1FEFFFFEA10100200"
    write_at_offset("Custom_ld_chagallbl_260027.bin",0x100,bytes.fromhex(loader))
    # prepare payload to 0x21000
    payload, _ = read_file_bytes("chagallbl_260027_bp_psb.bin")
    write_at_offset("Custom_ld_chagallbl_260027.bin",0x1100,payload)

    # create a new BIOS image
    copy_file("mc62g40-R14.rom", "mc62g40_R14_MilanLaunchy.rom")


    # well,mc62-g40 dnot have wpikek... let's inject it..
    # let's update total entries
    write_at_offset("mc62g40_R14_MilanLaunchy.rom",0x1180008,bytes.fromhex("18000000"))
    write_at_offset("mc62g40_R14_MilanLaunchy.rom",0x1180180,bytes.fromhex("21000000300000000000400100000000"))
    # now we plan to write wp_ikek in 0x1400000

    write_at_offset("mc62g40_R14_MilanLaunchy.rom",0x16c0008,bytes.fromhex("1d000000"))
    write_at_offset("mc62g40_R14_MilanLaunchy.rom",0x16c01d0,bytes.fromhex("21000000300000000000400100000000"))



    # this wpikek result to "b 0x20000"
    new_wpikek = "AA58809B67C0B7FB6559DE25258D74DAFC04578B7300D79EA97ACAC13676BAA0054E3A542CDD6878C35D2315131EEB93"
    write_at_offset("mc62g40_R14_MilanLaunchy.rom",0x1400000,bytes.fromhex(new_wpikek))


    write_at_offset("mc62g40_R14_MilanLaunchy.rom",0x1180030,bytes.fromhex("03000000000002000000410100000000"))
    # now we plan to write fw_rec in 0x1410000

    # let's update the checksum for pspdir
    verify_and_update_checksum("mc62g40_R14_MilanLaunchy.rom", checksum_offset=0x16C0004, data_start=0x16C0008, data_end=0x16C01E0)
    verify_and_update_checksum("mc62g40_R14_MilanLaunchy.rom", checksum_offset=0x1180004, data_start=0x1180008, data_end=0x1180190)


    # replace PSP_FW_RECOVERY_BOOT_LOADER
    recbl, _ = read_file_bytes("Milan_rec_bl_1001.bin")
    write_at_offset("mc62g40_R14_MilanLaunchy.rom",0x1410000,recbl)
    
    # replace PSP_FW_BOOT_LOADER 
    cus_bl, _ = read_file_bytes("Custom_ld_chagallbl_260027.bin")
    write_at_offset("mc62g40_R14_MilanLaunchy.rom",0x16c0400,cus_bl)

    # now let's create rbu file for easy bmc BIOS flash
    create_blank_file("mc62g40_R14_MilanLaunchy.RBU",0x2000000 + 0x10)
    checksum = calculate_checksum16_big_endian("mc62g40_R14_MilanLaunchy.rom")

    raw, _ = read_file_bytes("mc62g40_R14_MilanLaunchy.rom")
    write_at_offset("mc62g40_R14_MilanLaunchy.RBU",0,raw)
    write_at_offset("mc62g40_R14_MilanLaunchy.RBU",0x2000000,bytes.fromhex("2347425423524F4D"))
    write_at_offset("mc62g40_R14_MilanLaunchy.RBU",0x2000008,checksum)