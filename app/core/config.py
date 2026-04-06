from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Salesforce Validation Rule Switch"
    frontend_origin: str = "http://localhost:5173"
    api_base_url: str = "http://localhost:8000"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/cv_assignment"

    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 120

    salesforce_client_id: str = ""
    salesforce_client_secret: str = ""
    salesforce_redirect_uri: str = "http://localhost:8000/api/auth/callback"
    salesforce_login_url: str = "https://login.salesforce.com"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url.startswith("postgres://"):
            return self.database_url.replace("postgres://", "postgresql+psycopg://", 1)
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return self.database_url

    @property
    def effective_salesforce_redirect_uri(self) -> str:
        if self.salesforce_redirect_uri and "localhost" not in self.salesforce_redirect_uri:
            return self.salesforce_redirect_uri
        if self.api_base_url:
            return f"{self.api_base_url.rstrip('/')}/api/auth/callback"
        return self.salesforce_redirect_uri


settings = Settings()
