import unittest

from redpitaya_lock_host.custom_fpga_workflow import (
    CustomFpgaMeasurements,
    analyze_custom_fpga_measurements,
)


class CustomFpgaWorkflowTests(unittest.TestCase):
    def test_ratio_calculation(self) -> None:
        analysis = analyze_custom_fpga_measurements(
            CustomFpgaMeasurements(out1_error_vpp=0.2, out2_control_vpp=0.1)
        )
        self.assertAlmostEqual(analysis.out2_out1_ratio, 0.5)

    def test_out2_near_limit_is_danger(self) -> None:
        analysis = analyze_custom_fpga_measurements(
            CustomFpgaMeasurements(out1_error_vpp=0.1, out2_control_min=-0.81, out2_control_max=0.2)
        )
        self.assertEqual(analysis.level, "DANGER")

    def test_small_out1_is_warning(self) -> None:
        analysis = analyze_custom_fpga_measurements(
            CustomFpgaMeasurements(out1_error_vpp=0.001, out2_control_vpp=0.01)
        )
        self.assertEqual(analysis.level, "WARNING")


if __name__ == "__main__":
    unittest.main()
