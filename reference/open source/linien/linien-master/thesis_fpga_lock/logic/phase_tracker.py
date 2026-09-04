from migen import Module, Signal

from gateware.logic.cordic import Cordic


class PhaseTracker(Module):
    """Estimate signal phase from I/Q values.

    This is the module we will likely customize most heavily while following
    the thesis. For now it exposes the core vectoring primitive and a slot for
    a future smoothing stage.
    """

    def __init__(self, width=25):
        self.i_in = Signal((width, True))
        self.q_in = Signal((width, True))
        self.phase_out = Signal((width, True))
        self.magnitude_out = Signal((width, True))

        self.submodules.vector = Cordic(
            width=width,
            stages=width,
            guard=2,
            eval_mode="pipelined",
            cordic_mode="vector",
            func_mode="circular",
        )

        self.comb += [
            self.vector.xi.eq(self.i_in),
            self.vector.yi.eq(self.q_in),
            self.vector.zi.eq(0),
            self.magnitude_out.eq(self.vector.xo),
            self.phase_out.eq(self.vector.zo),
        ]
