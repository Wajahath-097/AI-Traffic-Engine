import sys

def extract_mpeg_ps(input_path, output_path):
    print(f"Reading from {input_path}")
    
    with open(input_path, 'rb') as f_in:
        # We know the first BA is at 41553420 from our previous mmap search, 
        # but let's be robust and search for the first Pack Header (00 00 01 BA).
        chunk_size = 10 * 1024 * 1024  # 10 MB chunks
        offset = 0
        found_offset = -1
        
        while True:
            chunk = f_in.read(chunk_size)
            if not chunk:
                break
                
            idx = chunk.find(b'\x00\x00\x01\xba')
            if idx != -1:
                found_offset = offset + idx
                break
                
            # Keep a small overlap just in case the start code spans across chunks
            offset += len(chunk) - 3
            f_in.seek(offset)
            
        if found_offset == -1:
            print("Could not find MPEG-PS Pack Header (00 00 01 BA) in the file.")
            
            # Fallback: Search for Video Elementary Stream (00 00 01 E0)
            f_in.seek(0)
            offset = 0
            while True:
                chunk = f_in.read(chunk_size)
                if not chunk:
                    break
                idx = chunk.find(b'\x00\x00\x01\xe0')
                if idx != -1:
                    found_offset = offset + idx
                    break
                offset += len(chunk) - 3
                f_in.seek(offset)
                
            if found_offset == -1:
                print("Could not find any Video Elementary Stream either. Aborting.")
                return
                
        print(f"Found MPEG-PS start at offset: {found_offset}")
        
        f_in.seek(found_offset)
        print(f"Extracting raw data to {output_path}...")
        
        with open(output_path, 'wb') as f_out:
            while True:
                chunk = f_in.read(chunk_size)
                if not chunk:
                    break
                f_out.write(chunk)
                
        print("Extraction complete!")

if __name__ == '__main__':
    in_file = r"F:\Recordings\2. KHAIRATABAD_ch10_20260917090115_20260917120230.mp4"
    out_file = r"d:\AI Traffic Engine\media\offline_videos\rescued_khairatabad.mpg"
    extract_mpeg_ps(in_file, out_file)
