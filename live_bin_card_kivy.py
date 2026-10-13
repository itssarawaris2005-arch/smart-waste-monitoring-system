"""Live BIN_001 sensor card — shared by admin and staff dashboards.

Reads the exact same Firebase path (bins/BIN_001) and the same fields
(status, fill_level, distance_cm, gps_valid, sensor_ok,
motion_events_since_boot, satellites, latitude, longitude, updated_at)
that admin_dashboard_kivy.py's live bin card uses, so both dashboards
show identical real-time hardware data.
"""

from datetime import datetime

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import Color, RoundedRectangle
from kivy.properties import ListProperty, NumericProperty
from kivy.metrics import dp, sp
from kivy.utils import get_color_from_hex

WHITE = get_color_from_hex("#FFFFFF")
DARK_GREEN = get_color_from_hex("#004D34")
TEXT_DARK = get_color_from_hex("#000000")
TEXT_GRAY = get_color_from_hex("#666666")
TEXT_GRAY2 = get_color_from_hex("#555555")
GREEN_FG = get_color_from_hex("#004D34")
RED_FG = get_color_from_hex("#D32F2F")
YELLOW_FG = get_color_from_hex("#F57C00")
CHART_LINE = get_color_from_hex("#39A96B")
GRID_LINE = get_color_from_hex("#EAEAEA")


class RoundedBox(BoxLayout):
    bg_color = ListProperty(list(WHITE))
    radius = NumericProperty(dp(14))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            self._bg_col = Color(*self.bg_color)
            self._bg_rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[self.radius],
            )
        self.bind(pos=self._sync, size=self._sync, bg_color=self._sync_color)

    def _sync(self, *_):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

    def _sync_color(self, *_):
        self._bg_col.rgba = self.bg_color


class FillBar(Widget):
    value = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            self._track_color = Color(*GRID_LINE)
            self._track = RoundedRectangle(radius=[dp(3)])
            self._fill_color = Color(*CHART_LINE)
            self._fill = RoundedRectangle(radius=[dp(3)])
        self.bind(pos=self._sync, size=self._sync, value=self._sync)

    def _sync(self, *_):
        self._track.pos = self.pos
        self._track.size = self.size
        width = self.width * max(0, min(100, self.value)) / 100
        self._fill.pos = self.pos
        self._fill.size = (width, self.height)


class LiveBinCard(RoundedBox):
    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            bg_color=list(WHITE),
            radius=dp(8),
            padding=(dp(13), dp(10)),
            spacing=dp(5),
            **kwargs,
        )

        header = BoxLayout(size_hint_y=None, height=dp(20))
        self.title_label = Label(
            text="BIN_001",
            font_size=sp(12.5),
            bold=True,
            color=DARK_GREEN,
            halign="left",
            valign="middle",
            text_size=(dp(180), dp(20)),
        )
        self.status_label = Label(
            text="CONNECTING",
            font_size=sp(10),
            bold=True,
            color=TEXT_GRAY,
            halign="right",
            valign="middle",
            text_size=(dp(120), dp(20)),
        )
        header.add_widget(self.title_label)
        header.add_widget(self.status_label)
        self.add_widget(header)

        metrics = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(18))
        self.fill_label = Label(
            text="--%\nFILL LEVEL",
            markup=True,
            font_size=sp(15),
            bold=True,
            color=TEXT_DARK,
            halign="left",
            valign="middle",
            text_size=(dp(135), dp(34)),
        )
        self.distance_label = Label(
            text="-- cm\nDISTANCE",
            markup=True,
            font_size=sp(15),
            bold=True,
            color=TEXT_DARK,
            halign="left",
            valign="middle",
            text_size=(dp(135), dp(34)),
        )
        metrics.add_widget(self.fill_label)
        metrics.add_widget(self.distance_label)
        self.add_widget(metrics)

        self.fill_bar = FillBar(
            size_hint_y=None,
            height=dp(6),
        )
        self.add_widget(self.fill_bar)

        self.health_label = Label(
            text="GPS --   |   SENSOR --   |   MOTION EVENTS --   |   SAT --",
            font_size=sp(8.5),
            bold=True,
            color=TEXT_GRAY2,
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(16),
            text_size=(dp(310), dp(16)),
        )
        self.location_label = Label(
            text="Location unavailable",
            font_size=sp(8.5),
            color=TEXT_GRAY,
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(15),
            text_size=(dp(310), dp(15)),
        )
        self.updated_label = Label(
            text="Waiting for live Firebase data",
            font_size=sp(8.5),
            color=TEXT_GRAY,
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(15),
            text_size=(dp(310), dp(15)),
        )
        self.device_label = Label(
            text="BIN FULL --   |   LED --   |   MOTION --   |   PIR --",
            font_size=sp(8.5),
            bold=True,
            color=TEXT_GRAY2,
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(16),
            text_size=(dp(310), dp(16)),
        )
        self.threshold_label = Label(
            text="FULL AT --%   |   RESET AT --%",
            font_size=sp(8.5),
            color=TEXT_GRAY,
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(15),
            text_size=(dp(310), dp(15)),
        )
        self.last_seen_label = Label(
            text="Last seen unavailable",
            font_size=sp(8.5),
            color=TEXT_GRAY,
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(15),
            text_size=(dp(310), dp(15)),
        )
        self.assignment_label = Label(
            text="Not assigned",
            font_size=sp(8.5),
            color=TEXT_GRAY,
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(15),
            text_size=(dp(310), dp(15)),
        )

        for label in (
            self.health_label,
            self.device_label,
            self.threshold_label,
            self.location_label,
            self.last_seen_label,
            self.updated_label,
            self.assignment_label,
        ):
            self.add_widget(label)

    @staticmethod
    def _value(record, key, suffix=""):
        value = record.get(key)
        if value is None or value == "":
            return "--"
        return f"{value}{suffix}"

    @staticmethod
    def _health(value):
        if value is None:
            return "--"
        return "OK" if bool(value) else "FAULT"

    @staticmethod
    def _timestamp(value):
        if not value:
            return "Update time unavailable"
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            return parsed.strftime("Updated %d %b %Y, %H:%M:%S UTC")
        except (TypeError, ValueError):
            return f"Updated {value}"

    @staticmethod
    def _yesno(value):
        if value is None:
            return "--"
        return "YES" if bool(value) else "NO"

    @staticmethod
    def _last_seen(value):
        if value in (None, ""):
            return "Last seen unavailable"
        try:
            parsed = datetime.fromtimestamp(float(value) / 1000.0)
            return parsed.strftime("Last seen %d %b %Y, %H:%M:%S")
        except (TypeError, ValueError, OSError):
            return f"Last seen {value}"

    def set_record(self, record):
        if not isinstance(record, dict):
            self.status_label.text = "UNAVAILABLE"
            self.status_label.color = RED_FG
            self.fill_label.text = "--%\nFILL LEVEL"
            self.distance_label.text = "-- cm\nDISTANCE"
            self.fill_bar.value = 0
            self.health_label.text = "GPS --   |   SENSOR --   |   MOTION EVENTS --   |   SAT --"
            self.device_label.text = "BIN FULL --   |   LED --   |   MOTION --   |   PIR --"
            self.threshold_label.text = "FULL AT --%   |   RESET AT --%"
            self.location_label.text = "Location unavailable"
            self.last_seen_label.text = "Last seen unavailable"
            self.updated_label.text = "Firebase data unavailable"
            self.assignment_label.text = "Not assigned"
            return

        status = str(record.get("status") or "unknown").upper()
        self.status_label.text = status
        self.status_label.color = (
            RED_FG if status == "FULL"
            else YELLOW_FG if status in ("HALF", "WARNING")
            else GREEN_FG
        )
        fill = record.get("fill_level")
        try:
            fill_number = max(0, min(100, float(fill)))
            fill_text = f"{fill_number:g}%"
        except (TypeError, ValueError):
            fill_number = 0
            fill_text = "--%"
        self.fill_label.text = f"{fill_text}\nFILL LEVEL"
        self.fill_bar.value = fill_number
        self.distance_label.text = (
            f"{self._value(record, 'distance_cm', ' cm')}\nDISTANCE"
        )
        self.health_label.text = (
            f"GPS {self._health(record.get('gps_valid'))}   |   "
            f"SENSOR {self._health(record.get('sensor_ok'))}   |   "
            f"MOTION EVENTS {self._value(record, 'motion_events_since_boot')}   |   "
            f"SAT {self._value(record, 'satellites')}"
        )
        self.location_label.text = (
            f"Location  {self._value(record, 'latitude')}, "
            f"{self._value(record, 'longitude')}"
        )
        self.device_label.text = (
            f"BIN FULL {self._yesno(record.get('bin_full'))}   |   "
            f"LED {self._yesno(record.get('led_on'))}   |   "
            f"MOTION {self._yesno(record.get('motion_detected'))}   |   "
            f"PIR {self._yesno(record.get('pir_ready'))}"
        )
        self.threshold_label.text = (
            f"FULL AT {self._value(record, 'full_threshold_percent', '%')}   |   "
            f"RESET AT {self._value(record, 'full_reset_percent', '%')}"
        )
        self.last_seen_label.text = self._last_seen(record.get("last_seen_ms"))
        self.updated_label.text = self._timestamp(record.get("updated_at"))

        worker_name = record.get("assigned_worker_name")
        worker_id = record.get("assigned_worker_id")
        assignment_status = record.get("assignment_status")
        if worker_name or worker_id:
            label = worker_name or worker_id
            if worker_name and worker_id:
                label = f"{worker_name} ({worker_id})"
            status_text = f" • {assignment_status}" if assignment_status else ""
            self.assignment_label.text = f"Assigned to {label}{status_text}"
        else:
            self.assignment_label.text = "Not assigned"
