from pathlib import Path

from oqpes.instance import generate_instance, load_instance, save_instance


def test_deterministic_generation():
    a = generate_instance(5, 10, 10, 1)
    b = generate_instance(5, 10, 10, 1)
    assert a.seed == b.seed
    assert a.digest() == b.digest()


def test_save_load_checksum(tmp_path: Path):
    inst = generate_instance(5, 10, 10, 2)
    p = tmp_path / "i.npz"
    save_instance(inst, p)
    got = load_instance(p)
    assert got.digest() == inst.digest()
