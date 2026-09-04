from migen import Module, Signal

from .config import ADC_WIDTH, COEFF_WIDTH, DAC_WIDTH, PHASE_WIDTH, SIGNAL_WIDTH
from .logic.dds import QuadratureDDS
from .logic.error_signal import ErrorSelector
from .logic.iq_demod import IQDemodulator
from .logic.phase_tracker import PhaseTracker
from .logic.pid_incremental import IncrementalPID
from .logic.scan_generator import TriangleScan


class ThesisLockTop(Module):
    """Top-level signal chain for the thesis-oriented FPGA project."""

    def __init__(self):
        self.adc_in = Signal((ADC_WIDTH, True))
        self.scan_out = Signal((DAC_WIDTH, True))
        self.mod_out = Signal((DAC_WIDTH, True))
        self.fast_out = Signal((DAC_WIDTH, True))
        self.slow_out = Signal((DAC_WIDTH, True))

        self.submodules.scan = TriangleScan(width=DAC_WIDTH)
        self.submodules.dds = QuadratureDDS(width=DAC_WIDTH, phase_width=PHASE_WIDTH)
        self.submodules.demod = IQDemodulator(
            adc_width=ADC_WIDTH,
            signal_width=SIGNAL_WIDTH,
            coeff_width=COEFF_WIDTH,
        )
        self.submodules.phase = PhaseTracker(width=SIGNAL_WIDTH)
        self.submodules.error = ErrorSelector(width=SIGNAL_WIDTH)
        self.submodules.fast_pid = IncrementalPID(
            width=SIGNAL_WIDTH, coeff_width=COEFF_WIDTH
        )
        self.submodules.slow_pid = IncrementalPID(
            width=SIGNAL_WIDTH, coeff_width=COEFF_WIDTH
        )

        self.comb += [
            self.scan_out.eq(self.scan.output),
            self.mod_out.eq(self.dds.sin_out),
            self.demod.adc_in.eq(self.adc_in),
            self.demod.ref_i.eq(self.dds.sin_out),
            self.demod.ref_q.eq(self.dds.cos_out),
            self.phase.i_in.eq(self.demod.i_out),
            self.phase.q_in.eq(self.demod.q_out),
            self.error.i_aligned.eq(self.demod.i_out),
            self.fast_pid.error_in.eq(self.error.error_out),
            self.slow_pid.error_in.eq(self.error.error_out),
            self.fast_out.eq(self.fast_pid.output[:DAC_WIDTH]),
            self.slow_out.eq(self.slow_pid.output[:DAC_WIDTH]),
        ]
