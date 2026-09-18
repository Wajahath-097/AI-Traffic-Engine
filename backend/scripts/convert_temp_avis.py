import os
import glob
import subprocess

def main():
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    video_dir = os.path.join(project_root, "media", "offline_videos")
    
    temp_avis = glob.glob(os.path.join(video_dir, "*_temp.avi"))
    
    if not temp_avis:
        print(f"No _temp.avi files found in {video_dir}")
        return
        
    for temp_avi in temp_avis:
        # Final output path (replace _temp.avi with _processed.mp4)
        final_out_path = temp_avi.replace('_temp.avi', '_processed.mp4')
        
        print(f"Converting to H.264 format: {final_out_path}")
        try:
            # Note: ffmpeg needs to be in PATH
            subprocess.run([
                "ffmpeg", "-y", "-i", temp_avi, 
                "-vf", "scale=-1:1080", 
                "-vcodec", "libx264", 
                "-pix_fmt", "yuv420p", 
                "-preset", "fast", 
                final_out_path
            ], check=True)
            
            # Clean up temp file
            if os.path.exists(temp_avi):
                os.remove(temp_avi)
                print(f"Successfully converted and cleaned up: {temp_avi}")
        except Exception as e:
            print(f"Error during ffmpeg conversion for {temp_avi}: {e}")

if __name__ == "__main__":
    main()
