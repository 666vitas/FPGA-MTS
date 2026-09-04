from migen import If, Module, Signal


class TriangleScan(Module):
    """Generate a signed triangle-wave scan signal.

    The scan value is intended for the slow tuning port, such as the laser PZT.
    Frequency is controlled by the step size relative to the system clock.
    """

    def __init__(self, width=14, step_width=32):
        self.enable = Signal()
        self.hold = Signal()
        self.step = Signal(step_width)
        self.min_value = Signal((width, True))
        self.max_value = Signal((width, True))
        self.output = Signal((width, True))
        self.rising = Signal(reset=1)

        accumulator = Signal((width + 1, True))

        self.sync += [
            If(
                ~self.enable,
                accumulator.eq(0),
                self.output.eq(0),
                self.rising.eq(1),
            ).Elif(
                ~self.hold,
                If(
                    self.rising,
                    If(
                        accumulator >= self.max_value,
                        self.rising.eq(0),
                    ).Else(
                        accumulator.eq(accumulator + self.step[:width]),
                    ),
                ).Else(
                    If(
                        accumulator <= self.min_value,
                        self.rising.eq(1),
                    ).Else(
                        accumulator.eq(accumulator - self.step[:width]),
                    ),
                ),
                self.output.eq(accumulator[:width]),
            )
        ]
