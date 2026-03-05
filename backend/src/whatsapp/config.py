from pydantic import BaseModel

headers = {
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "es-AR,es;q=0.8,en-US;q=0.5,en;q=0.3",
}

class WebConfig(BaseModel):
    headers: dict[str, str]

def get_web_config() -> WebConfig:
    return WebConfig(headers=headers)