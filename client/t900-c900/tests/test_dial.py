"""Unit tests for watch face dial compilation and RGB565 generation."""
import unittest
from t900_c900.dial import (
    rgb_to_rgb565_bytes,
    generate_solid_rgb565,
    generate_gradient_rgb565,
    compile_dial_package,
    parse_dial_package,
    DIAL_MAGIC,
    COLOR_FORMAT_RGB565,
)


class TestDial(unittest.TestCase):
    def test_rgb565_conversion(self):
        # Pure Black: (0, 0, 0) -> 0x0000
        self.assertEqual(rgb_to_rgb565_bytes(0, 0, 0), b"\x00\x00")
        # Pure White: (255, 255, 255) -> 0xFFFF
        self.assertEqual(rgb_to_rgb565_bytes(255, 255, 255), b"\xFF\xFF")
        # Pure Red: (255, 0, 0) -> 0xF800 (LE: 0x00, 0xF8)
        self.assertEqual(rgb_to_rgb565_bytes(255, 0, 0), b"\x00\xF8")
        # Pure Green: (0, 255, 0) -> 0x07E0 (LE: 0xE0, 0x07)
        self.assertEqual(rgb_to_rgb565_bytes(0, 255, 0), b"\xE0\x07")
        # Pure Blue: (0, 0, 255) -> 0x001F (LE: 0x1F, 0x00)
        self.assertEqual(rgb_to_rgb565_bytes(0, 0, 255), b"\x1F\x00")

    def test_compile_and_parse_dial_package(self):
        dial_data = compile_dial_package(width=240, height=286, thumb_width=64, thumb_height=64)
        parsed = parse_dial_package(dial_data)

        self.assertEqual(parsed["version"], 1)
        self.assertEqual(parsed["width"], 240)
        self.assertEqual(parsed["height"], 286)
        self.assertEqual(parsed["thumbnail_size"], 64 * 64 * 2)
        self.assertEqual(parsed["background_size"], 240 * 286 * 2)
        self.assertEqual(len(parsed["background_bytes"]), 240 * 286 * 2)

    def test_dial_size_mismatch_validation(self):
        with self.assertRaises(ValueError):
            compile_dial_package(width=240, height=286, background_rgb565=b"too short")


if __name__ == "__main__":
    unittest.main()
