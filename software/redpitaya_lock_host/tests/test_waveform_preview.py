import unittest

import numpy as np

from redpitaya_lock_host.waveform_preview import (
    PreviewConfig,
    generate_waveform,
    generate_waveform_preview,
    make_preview_time_axis,
)


class WaveformPreviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = PreviewConfig(cycles=2, min_points=1024, max_points=5000)

    def test_50_hz_preview_covers_at_least_two_cycles(self) -> None:
        t = make_preview_time_axis(50.0, cycles=2, min_points=1024, max_points=5000)
        self.assertGreaterEqual(t[-1] - t[0], 0.04)
        self.assertLessEqual(t.size, self.config.max_points)

    def test_triangle_min_max_match_offset_plus_minus_amplitude(self) -> None:
        t = make_preview_time_axis(50.0, cycles=2, min_points=1024, max_points=5000)
        y = generate_waveform(t, "triangle", 50.0, 0.05, 0.01, 0.0)
        self.assertTrue(np.isclose(np.nanmin(y), -0.04, atol=2e-4))
        self.assertTrue(np.isclose(np.nanmax(y), 0.06, atol=2e-4))

    def test_supported_waveforms_generate_nonempty_data(self) -> None:
        for waveform in ("sine", "square", "triangle", "sawtooth"):
            with self.subTest(waveform=waveform):
                t, y = generate_waveform_preview(waveform, 123.0, 0.1, 0.0, 15.0, self.config)
                self.assertGreater(t.size, 0)
                self.assertEqual(t.size, y.size)
                self.assertGreaterEqual(t.size, self.config.min_points)
                self.assertLessEqual(t.size, self.config.max_points)
                self.assertTrue(np.all(np.isfinite(y)))


if __name__ == "__main__":
    unittest.main()
