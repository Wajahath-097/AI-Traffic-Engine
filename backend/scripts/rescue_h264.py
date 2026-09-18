import os
import struct

def rescue_avcc_to_annexb(input_path, output_path, max_nal_units=10000):
    with open(input_path, 'rb') as f:
        # Skip ftyp and find mdat
        data = f.read(1024)
        mdat_idx = data.find(b'mdat')
        if mdat_idx == -1:
            print("mdat not found in first 1KB")
            return
            
        # The mdat header is usually 'mdat' + 64-bit size or 32-bit size.
        # From our hex dump: 00 00 00 01 6d 64 61 74 [8 bytes size]
        # We know mdat starts at mdat_idx. The data starts at mdat_idx + 4 + 8 (if 64-bit).
        # Let's seek to mdat_idx + 4
        f.seek(mdat_idx + 4)
        
        # In our hex dump, the 8 bytes after mdat were 00 00 00 01 ff b7 24 4d
        # Then the first NAL unit size was 00 00 00 1a
        size_bytes = f.read(8)
        
        with open(output_path, 'wb') as out_f:
            nal_count = 0
            while nal_count < max_nal_units:
                size_buf = f.read(4)
                if len(size_buf) < 4:
                    break
                
                # AVCC is big-endian length
                nal_size = struct.unpack('>I', size_buf)[0]
                
                # Sanity check on nal_size to prevent allocating too much if corrupt
                if nal_size == 0 or nal_size > 10 * 1024 * 1024:
                    print(f"Suspicious NAL size {nal_size} at NAL {nal_count}. Stopping.")
                    break
                    
                nal_data = f.read(nal_size)
                if len(nal_data) < nal_size:
                    break
                
                # Write Annex B start code + NAL data
                out_f.write(b'\x00\x00\x00\x01' + nal_data)
                nal_count += 1
                
    print(f"Extracted {nal_count} NAL units to {output_path}")

if __name__ == "__main__":
    in_file = r"F:\Recordings\2. KHAIRATABAD_ch10_20260917090115_20260917120230.mp4"
    out_file = r"d:\AI Traffic Engine\media\offline_videos\rescued_test.h264"
    rescue_avcc_to_annexb(in_file, out_file)
