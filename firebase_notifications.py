"""In-app notifications driven by the live BIN_001 Firebase record."""

import threading

from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup

from firebase_auth import get_current_user
from firebase_config import get_data


BIN_PATH = "bins/BIN_001"
POLL_SECONDS = 3


def _unwrap(result):
    if isinstance(result, tuple) and len(result) >= 2:
        return bool(result[0]), result[1]
    return True, result


class FirebaseNotificationWatcher:
    DEFAULT_SETTINGS = {
        "push_notifications": True,
        "bin_full_alerts": True,
        "route_alerts": True,
    }

    def __init__(self):
        self._event = None
        self._running = False
        self._previous = None
        self._popup = None

    def start(self):
        if self._event is None:
            self._event = Clock.schedule_interval(
                self._schedule_poll,
                POLL_SECONDS,
            )
        self._schedule_poll()

    def stop(self):
        if self._event is not None:
            self._event.cancel()
            self._event = None
        self._previous = None

    def _schedule_poll(self, *_):
        if self._running or not get_current_user():
            return
        self._running = True
        threading.Thread(target=self._poll, daemon=True).start()

    def _poll(self):
        try:
            ok, record = _unwrap(get_data(BIN_PATH))
            if not ok or not isinstance(record, dict):
                return

            settings = self._load_settings()
            messages = self._detect_changes(record, settings)
            if messages:
                Clock.schedule_once(
                    lambda dt, items=messages: self._show(items),
                    0,
                )
        except Exception as exc:
            print("[NOTIFICATIONS] Firebase watcher error:", exc)
        finally:
            self._running = False

    def _load_settings(self):
        settings = dict(self.DEFAULT_SETTINGS)
        user = get_current_user() or {}
        uid = user.get("localId") or user.get("uid")
        if not uid:
            return settings

        ok, data = _unwrap(
            get_data(f"admin/{uid}/notification_settings")
        )
        if ok and isinstance(data, dict):
            for key in settings:
                if key in data:
                    settings[key] = bool(data[key])
        return settings

    @staticmethod
    def _is_full(record):
        if record.get("bin_full") is True:
            return True
        try:
            level = float(record.get("fill_level"))
            threshold = float(record.get("full_threshold_percent", 90))
            return level >= threshold
        except (TypeError, ValueError):
            return str(record.get("status") or "").lower() == "full"

    def _detect_changes(self, record, settings):
        try:
            motion_count = int(record.get("motion_events_since_boot"))
        except (TypeError, ValueError):
            motion_count = None

        current = {
            "full": self._is_full(record),
            "motion_count": motion_count,
            "sensor_ok": record.get("sensor_ok") is not False,
            "gps_valid": record.get("gps_valid") is not False,
        }
        previous = self._previous
        self._previous = current

        if not settings.get("push_notifications", True):
            return []

        messages = []
        first_read = previous is None

        if settings.get("bin_full_alerts", True):
            if current["full"] and (first_read or not previous["full"]):
                messages.append("BIN_001 is full and needs collection.")
            elif previous and previous["full"] and not current["full"]:
                messages.append("BIN_001 is no longer full.")

        if previous:
            old_count = previous.get("motion_count")
            new_count = current.get("motion_count")
            if (
                old_count is not None
                and new_count is not None
                and new_count > old_count
            ):
                increase = new_count - old_count
                suffix = "event" if increase == 1 else "events"
                messages.append(
                    f"Motion sensed at BIN_001 ({increase} new {suffix})."
                )

        if previous and previous["sensor_ok"] and not current["sensor_ok"]:
            messages.append("BIN_001 sensor reported a fault.")
        elif previous and not previous["sensor_ok"] and current["sensor_ok"]:
            messages.append("BIN_001 sensor is working again.")

        if settings.get("route_alerts", True):
            if previous and previous["gps_valid"] and not current["gps_valid"]:
                messages.append("BIN_001 GPS signal was lost.")
            elif previous and not previous["gps_valid"] and current["gps_valid"]:
                messages.append("BIN_001 GPS signal was restored.")

        return messages

    def _show(self, messages):
        if self._popup is not None:
            self._popup.dismiss()

        content = BoxLayout(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(12),
        )
        with content.canvas.before:
            Color(1, 1, 1, 1)
            background = RoundedRectangle(
                pos=content.pos,
                size=content.size,
                radius=[dp(6)],
            )
        content.bind(
            pos=lambda widget, *_: setattr(background, "pos", widget.pos),
            size=lambda widget, *_: setattr(background, "size", widget.size),
        )

        label = Label(
            text="\n".join(messages),
            color=(0.08, 0.10, 0.09, 1),
            font_size=sp(13),
            halign="left",
            valign="middle",
        )
        label.bind(size=lambda widget, *_: setattr(widget, "text_size", widget.size))
        content.add_widget(label)

        close_button = Button(
            text="Dismiss",
            size_hint_y=None,
            height=dp(40),
            background_normal="",
            background_color=(0, 0.30, 0.20, 1),
        )
        content.add_widget(close_button)

        self._popup = Popup(
            title="Live Bin Alert",
            content=content,
            size_hint=(0.88, None),
            height=dp(230),
            auto_dismiss=True,
        )
        close_button.bind(on_release=self._popup.dismiss)
        self._popup.bind(on_dismiss=lambda *_: setattr(self, "_popup", None))
        self._popup.open()


notification_watcher = FirebaseNotificationWatcher()
