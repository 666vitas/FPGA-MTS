from migen import If, Module, Signal

from gateware.logic.cordic import Cordic


class QuadratureDDS(Module):
    """Generate sine and cosine references for modulation and demodulation."""

    def __init__(self, width=14, phase_width=32):
        self.enable = Signal()
        self.phase_step = Signal(phase_width)
        self.phase_offset = Signal(phase_width)
        self.amplitude = Signal((width, True))

        self.phase = Signal(phase_width)
        self.sin_out = Signal((width, True))
        self.cos_out = Signal((width, True))

        self.sync += [
            If(~self.enable, self.phase.eq(self.phase_offset)).Else(
                self.phase.eq(self.phase + self.phase_step)
            )
        ]

        self.submodules.sin_cordic = Cordic(
            width=width + 1,
            stages=width + 1,
            guard=2,
            eval_mode="pipelined",
            cordic_mode="rotate",
            func_mode="circular",
        )
        self.submodules.cos_cordic = Cordic(
            width=width + 1,
            stages=width + 1,
            guard=2,
            eval_mode="pipelined",
            cordic_mode="rotate",
            func_mode="circular",
        )

        self.comb += [
            self.sin_cordic.xi.eq(self.amplitude),
            self.sin_cordic.zi.eq(self.phase[:width] << 1),
            self.sin_out.eq(self.sin_cordic.yo >> 1),
            self.cos_cordic.xi.eq(self.amplitude),
            self.cos_cordic.zi.eq((self.phase[:width] + (1 << (width - 2))) << 1),
            self.cos_out.eq(self.cos_cordic.yo >> 1),
        ]
