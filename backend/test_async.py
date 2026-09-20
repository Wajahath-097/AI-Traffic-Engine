import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.routers.cameras import get_camera_snapshot

async def main():
    try:
        resp = await get_camera_snapshot("CAM01")
        print(f"Status: {resp.status_code}")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
