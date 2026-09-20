import asyncio
import httpx

async def main():
    url = "http://103.250.160.189:8889/stream/cam01/whep"
    auth = ("mdwajahathullahshareef@gmail.com", "LFQP-568P-M28D")
    dummy_offer = "v=0\r\no=- 0 0 IN IP4 127.0.0.1\r\ns=-\r\nt=0 0\r\n"
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            content=dummy_offer,
            headers={"Content-Type": "application/sdp"},
            auth=auth,
            timeout=5.0
        )
    print(resp.status_code)
    print(resp.text)

asyncio.run(main())
