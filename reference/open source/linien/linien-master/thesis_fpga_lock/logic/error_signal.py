from migen import Module, Signal


class ErrorSelector(Module):
    """Expose the lock error signal after phase alignment.

    In the thesis flow, the in-phase demodulated component after phase matching
    becomes the error signal that feeds both PID loops.
    """

    def __init__(self, width=25):
        self.i_aligned = Signal((width, True))
        self.error_out = Signal((width, True))

        self.comb += self.error_out.eq(self.i_aligned)
