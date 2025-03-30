from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OKTA_DOMAIN: str
    OKTA_CLIENT_ID: str
    OKTA_CLIENT_SECRET: str
    API_BASE_URL: str = "http://localhost:8000"
    SESSION_TIMEOUT: int = 600  # 10분
    STREAMLIT_SERVER_ADDRESS: str = "localhost"  # 추가
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # 정의되지 않은 환경 변수 무시

settings = Settings() 