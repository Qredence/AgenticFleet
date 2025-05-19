from dataclasses import dataclass, field


@dataclass
class EnvironmentConfig:
    debug: bool = False
    workspace_dir: str = "./.files/workspace"
    downloads_dir: str = "./.files/downloads"
    debug_dir: str = "./.files/debug"
    logs_dir: str = "./.files/logs"
    stream_delay: float = 0.01


@dataclass
class DefaultsConfig:
    max_rounds: int = 10
    max_time: int = 300
    max_stalls: int = 3
    start_page: str = "https://www.bing.com"
    temperature: float = 0.7
    system_prompt: str = "You are a helpful AI assistant."


@dataclass
class OAuthProviderConfig:
    name: str
    client_id_env: str
    client_secret_env: str


@dataclass
class SecurityConfig:
    use_oauth: bool = True
    oauth_providers: list[OAuthProviderConfig] = field(default_factory=list)


@dataclass
class ApiConfig:
    prefix: str = "/api"
    host: str = "0.0.0.0"
    port: int = 8000


@dataclass
class CorsConfig:
    origins: str = "*"
    credentials: bool = True
    methods: str = "GET,POST,PUT,DELETE,OPTIONS"
    headers: str = "Content-Type,Authorization"


@dataclass
class LoggingConfig:
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
