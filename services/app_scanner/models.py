from dataclasses import dataclass, field


@dataclass
class App:
    name: str
    path: str
    source: str
    confidence: float


@dataclass
class ScanResult:
    apps: list[App]
    source: str
    elapsed: float
