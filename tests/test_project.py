from pathlib import Path


def test_clickable_launcher_exists():
    root = Path(__file__).resolve().parents[1]
    assert (root / "START_OQPES.bat").exists()
    assert (root / "environment.yml").exists()
