from pydantic_settings import BaseSettings, SettingsConfigDict



class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    db_name: str
    db_user: str
    db_password: str
    db_port: int
    db_host: str
    @property
    def database_url(self)-> str:
        return f'postgresql+psycopg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}'

settings = Settings()