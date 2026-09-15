from __future__ import annotations

import platform
from typing import Callable, Optional


class PycawAudioBackend:
	"""Small adapter around pycaw so the switching logic remains testable."""

	def __init__(self):
		from pycaw.constants import DEVICE_STATE, EDataFlow, ERole
		from pycaw.pycaw import AudioUtilities

		self._device_state = DEVICE_STATE
		self._data_flow = EDataFlow
		self._roles = ERole
		self._audio_utilities = AudioUtilities

	def get_default_output(self):
		return self._audio_utilities.GetSpeakers()

	def get_active_outputs(self):
		return self._audio_utilities.GetAllDevices(
			data_flow=self._data_flow.eRender.value,
			device_state=self._device_state.ACTIVE.value,
		)

	def set_default_output(self, device_id: str):
		self._audio_utilities.SetDefaultDevice(
			device_id,
			roles=[self._roles.eConsole, self._roles.eMultimedia],
		)


class FlooAudioOutputSwitcher:
	IDLE_STATE = 1
	DISCONNECTING_STATE = 8
	CONNECTED_STATES = frozenset((4, 5, 6, 7, 9, 10, 11))
	TARGET_NAME_PARTS = ("fma120", "floogoo")

	def __init__(
		self,
		enabled: bool = False,
		backend=None,
		error_callback: Optional[Callable[[str], None]] = None,
		system_name: Optional[str] = None,
	):
		self.enabled = enabled
		self._backend = backend
		self._error_callback = error_callback
		self._is_windows = (system_name or platform.system()).lower().startswith("win")
		self._headset_connected = False
		self._previous_device_id = None
		self._target_device_id = None

	@property
	def supported(self) -> bool:
		return self._is_windows

	def set_enabled(self, enabled: bool):
		if not enabled:
			self._headset_connected = False
			self._previous_device_id = None
			self._target_device_id = None
		self.enabled = enabled

	def handle_source_state(self, state: Optional[int]):
		if not self.enabled or not self.supported or state is None:
			return

		print("[AudioOutputSwitcher] FlooGoo source state: " + str(state))
		if state in self.CONNECTED_STATES and not self._headset_connected:
			self._headset_connected = True
			self._switch_to_floogoo()
		elif state in (self.DISCONNECTING_STATE, self.IDLE_STATE) and self._headset_connected:
			self._headset_connected = False
			self._restore_previous_output()

	def _get_backend(self):
		if self._backend is None:
			try:
				self._backend = PycawAudioBackend()
			except Exception as exc:
				raise RuntimeError(
					"pycaw is unavailable; install the Windows requirements and restart FlooCast"
				) from exc
		return self._backend

	def _switch_to_floogoo(self):
		try:
			backend = self._get_backend()
			current = backend.get_default_output()
			active_outputs = backend.get_active_outputs()
			target = self._find_target(active_outputs)
			if target is None:
				active_names = ", ".join(
					device.FriendlyName or "<unnamed>" for device in active_outputs
				)
				raise RuntimeError(
					"no active FMA120/FlooGoo audio output was found; active outputs: " +
					(active_names or "none")
				)

			self._target_device_id = target.id
			if current is not None and current.id == target.id:
				self._previous_device_id = None
				print(
					"[AudioOutputSwitcher] FMA120 is already the default output; "
					"there is no previous output to restore"
				)
				return

			self._previous_device_id = current.id if current is not None else None
			print(
				"[AudioOutputSwitcher] Switching from " +
				((current.FriendlyName or "<unnamed>") if current is not None else "<none>") +
				" to " + (target.FriendlyName or "<unnamed>")
			)
			backend.set_default_output(target.id)
		except Exception as exc:
			self._previous_device_id = None
			self._report_error(str(exc))

	def _restore_previous_output(self):
		if self._previous_device_id is None:
			return

		try:
			backend = self._get_backend()
			current = backend.get_default_output()
			if current is not None and current.id == self._target_device_id:
				print("[AudioOutputSwitcher] Restoring the previous Windows output")
				backend.set_default_output(self._previous_device_id)
			else:
				print(
					"[AudioOutputSwitcher] Default output changed manually; "
					"leaving it unchanged"
				)
		except Exception as exc:
			self._report_error(str(exc))
		finally:
			self._previous_device_id = None
			self._target_device_id = None

	def _find_target(self, devices):
		for device in devices:
			name = (device.FriendlyName or "").casefold()
			if any(part in name for part in self.TARGET_NAME_PARTS):
				return device
		return None

	def _report_error(self, message: str):
		print("Audio output switching failed: " + message)
		if self._error_callback is not None:
			self._error_callback(message)
