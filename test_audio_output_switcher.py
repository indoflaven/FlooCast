import unittest

from FlooAudioOutputSwitcher import FlooAudioOutputSwitcher


class FakeDevice:
	def __init__(self, device_id, name):
		self.id = device_id
		self.FriendlyName = name


class FakeBackend:
	def __init__(self, default_device, devices):
		self.default_device = default_device
		self.devices = devices
		self.switches = []

	def get_default_output(self):
		return self.default_device

	def get_active_outputs(self):
		return self.devices

	def set_default_output(self, device_id):
		self.switches.append(device_id)
		self.default_device = next(device for device in self.devices if device.id == device_id)


class FlooAudioOutputSwitcherTests(unittest.TestCase):
	def setUp(self):
		self.speakers = FakeDevice("speakers", "Realtek Speakers")
		self.floogoo = FakeDevice("floogoo", "Speakers (FMA120)")
		self.backend = FakeBackend(self.speakers, [self.speakers, self.floogoo])
		self.errors = []
		self.switcher = FlooAudioOutputSwitcher(
			enabled=True,
			backend=self.backend,
			error_callback=self.errors.append,
			system_name="Windows",
		)

	def test_connected_switches_and_idle_restores(self):
		self.switcher.handle_source_state(4)
		self.switcher.handle_source_state(6)
		self.switcher.handle_source_state(8)
		self.assertEqual(["floogoo", "speakers"], self.backend.switches)
		self.switcher.handle_source_state(1)

		self.assertEqual(["floogoo", "speakers"], self.backend.switches)
		self.assertEqual([], self.errors)

	def test_does_not_restore_over_manual_change(self):
		other = FakeDevice("other", "Display Audio")
		self.backend.devices.append(other)
		self.switcher.handle_source_state(4)
		self.backend.default_device = other
		self.switcher.handle_source_state(1)

		self.assertEqual(["floogoo"], self.backend.switches)

	def test_disabled_switcher_does_nothing(self):
		self.switcher.set_enabled(False)
		self.switcher.handle_source_state(4)

		self.assertEqual([], self.backend.switches)

	def test_non_windows_switcher_does_nothing(self):
		switcher = FlooAudioOutputSwitcher(
			enabled=True,
			backend=self.backend,
			system_name="Linux",
		)
		switcher.handle_source_state(4)

		self.assertEqual([], self.backend.switches)

	def test_missing_floogoo_reports_error(self):
		self.backend.devices = [self.speakers]
		self.switcher.handle_source_state(4)

		self.assertEqual([], self.backend.switches)
		self.assertIn("no active FMA120/FlooGoo", self.errors[0])
		self.assertIn("Realtek Speakers", self.errors[0])

	def test_floogoo_friendly_name_is_recognized(self):
		self.floogoo.FriendlyName = "FlooGoo USB Audio"
		self.switcher.handle_source_state(4)

		self.assertEqual(["floogoo"], self.backend.switches)


if __name__ == "__main__":
	unittest.main()
