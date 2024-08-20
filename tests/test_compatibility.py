import hashlib
from urllib.request import urlopen

import pytest


def version_hash(url: str) -> str:
    remote = urlopen(url)
    max_file_size = 100 * 1024 * 1024
    h = hashlib.sha256()
    total_read = 0
    while True:
        data = remote.read(4096)
        total_read += 4096
        if not data or total_read > max_file_size:
            break
        h.update(data)
    return h.hexdigest()


@pytest.fixture
def versions() -> list[str]:
    return [
        "2024.8.0",
        "2024.8.1",
        "2024.8.2",
    ]


@pytest.fixture
def shas(versions: list[str]) -> list[tuple[str, str]]:
    return [
        (
            v,
            version_hash(
                f"https://raw.githubusercontent.com/home-assistant/core/{v}/homeassistant/components/generic_thermostat/climate.py"
            ),
        )
        for v in versions
    ]


def test_compatibility(shas: list[tuple[str, str]]):
    for version, sha in shas:
        assert sha in [
            "257e182701edbccfdd474c1b2d7fc6ee508e77e4b52deb2d4db0ef372eadf808"
        ], f"Version {version} not in sha list"
