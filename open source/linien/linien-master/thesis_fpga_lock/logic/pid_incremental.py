from migen import Module, Signal


class IncrementalPID(Module):
    """Incremental PID skeleton.

    We keep this intentionally small at first so we can derive the exact fixed-
    point equation together from the thesis before tuning overflow behavior.
    """

    def __init__(self, width=25, coeff_width=18):
        self.error_in = Signal((width, True))
        self.enable = Signal()
        self.kp = Signal((coeff_width, True))
        self.ki = Signal((coeff_width, True))
        self.kd = Signal((coeff_width, True))
        self.output = Signal((width, True))

        prev_error = Signal((width, True))
        prev_prev_error = Signal((width, True))
        delta = Signal((width, True))
        accumulator = Signal((width, True))

        self.sync += [
            delta.eq(
                (self.kp * (self.error_in - prev_error))
                + (self.ki * self.error_in)
                + (self.kd * (self.error_in - (prev_error << 1) + prev_prev_error))
            ),
            prev_prev_error.eq(prev_error),
            prev_error.eq(self.error_in),
            accumulator.eq(accumulator + delta),
            self.output.eq(accumulator if self.enable else 0),
        ]
