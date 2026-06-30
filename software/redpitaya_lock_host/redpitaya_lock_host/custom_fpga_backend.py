"""Future Custom FPGA register/debug backend.

This module intentionally does not return fake FPGA data. Real implementations
require an RTL register bank, debug buffer, or AXI-accessible readout path.
"""

from __future__ import annotations


NOT_IMPLEMENTED = "Custom FPGA register/debug interface is not implemented yet"


class CustomFpgaBackend:
    def read_status(self):
        raise NotImplementedError(NOT_IMPLEMENTED)

    def read_error_snapshot(self):
        raise NotImplementedError(NOT_IMPLEMENTED)

    def read_control_snapshot(self):
        raise NotImplementedError(NOT_IMPLEMENTED)

    def set_mode_safe(self):
        raise NotImplementedError(NOT_IMPLEMENTED)

    def set_mode_hold(self):
        raise NotImplementedError(NOT_IMPLEMENTED)

    def set_pid_params(self, *args, **kwargs):
        raise NotImplementedError(NOT_IMPLEMENTED)

    def set_output_limit(self, *args, **kwargs):
        raise NotImplementedError(NOT_IMPLEMENTED)
