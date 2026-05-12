from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings for the Precaution Definer Agent.
    Loads values from environment variables or a .env file.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o"
    openai_max_turns: int = 100

    # Main Operational Database (READ + WRITE)
    main_db_host: str
    main_db_port: int = 5432
    main_db_name: str = "postgres"
    main_db_user: str = "postgres"
    main_db_password: str
    main_db_pool_min: int = 2
    main_db_pool_max: int = 10

    # Collection Database (READ ONLY)
    collection_db_host: str
    collection_db_port: int = 5432
    collection_db_name: str = "postgres"
    collection_db_user: str = "postgres"
    collection_db_password: str
    collection_db_pool_min: int = 2
    collection_db_pool_max: int = 5

    # Service
    app_port: int = 8003
    app_env: str = "production"
    log_level: str = "INFO"
    service_name: str = "climasync-precaution-definer-agent"

    # Security
    internal_api_key: str

    # Downstream
    work_distributor_base_url: str = "http://localhost:8004"
    work_distributor_api_key: str

    # Pakistan Constants
    pakistan_avg_household_size: float = 6.5
    formal_shelter_ratio: float = 0.60
    who_water_liters_per_person: float = 15.0
    tanker_capacity_liters: int = 10000


# Create a singleton instance to be imported throughout the application
settings = Settings()
