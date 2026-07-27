from migen import Module, Signal

from gateware.logic.iir import Iir


class IQDemodulator(Module):
    """Demodulate an ADC signal with quadrature references."""

    def __init__(self, adc_width=14, signal_width=25, coeff_width=18):
        self.adc_in = Signal((adc_width, True))
        self.ref_i = Signal((adc_width, True))
        self.ref_q = Signal((adc_width, True))

        self.mix_i = Signal((signal_width, True))
        self.mix_q = Signal((signal_width, True))
        self.i_out = Signal((signal_width, True))
        self.q_out = Signal((signal_width, True))

        self.submodules.i_lpf = Iir(
            width=signal_width,
            coeff_width=coeff_width,
            shift=coeff_width - 2,
            order=2,
        )
        self.submodules.q_lpf = Iir(
            width=signal_width,
            coeff_width=coeff_width,
            shift=coeff_width - 2,
            order=2,
        )

        self.comb += [
            self.mix_i.eq(self.adc_in * self.ref_i),
            self.mix_q.eq(self.adc_in * self.ref_q),
            self.i_lpf.x.eq(self.mix_i),
            self.i_lpf.hold.eq(0),
            self.i_lpf.clear.eq(0),
            self.q_lpf.x.eq(self.mix_q),
            self.q_lpf.hold.eq(0),
            self.q_lpf.clear.eq(0),
            self.i_out.eq(self.i_lpf.y),
            self.q_out.eq(self.q_lpf.y),
        ]
