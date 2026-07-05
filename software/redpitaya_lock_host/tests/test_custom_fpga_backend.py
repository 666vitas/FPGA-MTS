from redpitaya_lock_host.custom_fpga_backend import (
    status_payload_has_expected_magic,
    missing_magic_guidance,
)


def test_status_payload_rejects_zero_magic_string() -> None:
    payload = {"magic": "0x00000000", "version": "0x00000000"}

    assert not status_payload_has_expected_magic(payload)
    assert "no custom_register_bank was read" in missing_magic_guidance(payload["magic"])


def test_status_payload_accepts_expected_magic_string() -> None:
    payload = {"magic": "0x4D545330"}

    assert status_payload_has_expected_magic(payload)
