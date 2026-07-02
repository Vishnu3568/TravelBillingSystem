import os

class Settings:
    PORT: int = int(os.getenv("PORT", 9000))
    JWT_SECRET: str = os.getenv("JWT_SECRET", "travel-billing-default-secret-key-change-me-please-32chars")
    JWT_EXPIRATION_MS: int = int(os.getenv("JWT_EXPIRATION_MS", 86400000))
    
    # AI Integration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
    AI_SERVICE_URL: str = os.getenv("AI_SERVICE_URL", "http://localhost:9001/api/ai")
    INTERNAL_API_KEY: str = os.getenv("INTERNAL_API_KEY", "")

    # Database
    DB_URL: str = os.getenv("DB_URL", "jdbc:mysql://localhost:3306/travelbillingdb?useSSL=false&serverTimezone=Asia/Kolkata&allowPublicKeyRetrieval=true")
    DB_USERNAME: str = os.getenv("DB_USERNAME", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "root")

    @property
    def sqlalchemy_database_url(self) -> str:
        jdbc_url = self.DB_URL
        user = self.DB_USERNAME
        password = self.DB_PASSWORD
        
        # If it is a jdbc url, extract components
        if jdbc_url.startswith("jdbc:mysql://"):
            # strip jdbc:mysql://
            clean_url = jdbc_url[len("jdbc:mysql://"):]
            
            # split query params
            parts = clean_url.split("?")
            host_port_db = parts[0]
            
            # split host/port and dbname
            if "/" in host_port_db:
                host_port, dbname = host_port_db.split("/", 1)
            else:
                host_port = host_port_db
                dbname = "travelbillingdb"
            
            if "@" in host_port:
                creds, host_port = host_port.split("@", 1)
                if ":" in creds:
                    user, password = creds.split(":", 1)
                else:
                    user = creds
            
            return f"mysql+pymysql://{user}:{password}@{host_port}/{dbname}"
        elif jdbc_url.startswith("mysql://"):
            return jdbc_url.replace("mysql://", "mysql+pymysql://", 1)
        elif jdbc_url.startswith("mysql+pymysql://"):
            return jdbc_url
            
        return f"mysql+pymysql://{user}:{password}@localhost:3306/travelbillingdb"

    @property
    def is_dev(self) -> bool:
        return os.getenv("ENV", "dev").lower() == "dev"

settings = Settings()
