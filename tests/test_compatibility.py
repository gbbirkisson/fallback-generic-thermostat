import hashlib
import optparse
import os
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
        "2023.8.4",
        "2023.9.0",
        "2023.9.1",
        "2023.9.2",
        "2023.9.3",
        "2023.10.5",
        "2023.11.0",
        "2023.11.1",
        "2023.11.2",
        "2023.11.3",
        "2023.12.0",
        "2023.12.1",
        "2023.12.2",
        "2023.12.3",
        "2023.12.4",
        "2024.1.0",
        "2024.1.1",
        "2024.1.2",
        "2024.1.3",
        "2024.1.4",
        "2024.1.5",
        "2024.1.6",
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
            "4aeb00650cdbf1d1aa526e84bbdf4ecf228d0f62341e6589fd97d37748273712",
            "6f6b213280807f31643d0294aea857d959c17bf70c83159c62f6e439978eca54",
        ], f"Version {version} not in sha list"
