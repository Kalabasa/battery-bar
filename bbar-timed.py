#!/usr/bin/python

import os, gobject, dbus
from dbus.mainloop.glib import DBusGMainLoop
import gtk
import pygtk
pygtk.require('2.0')
import cairo
import math
import time

UPOWER_BUSNAME = 'org.freedesktop.UPower'
UPOWER_DEVICE_IFACE = 'org.freedesktop.UPower.Device'
UPOWER_BATTERY_OBJECT = '/org/freedesktop/UPower/devices/battery_BATA'

STATE_UNKNOWN = 0
STATE_CHARGING = 1
STATE_DISCHARGING = 2
STATE_EMPTY = 3
STATE_FULLY_CHARGED = 4
STATE_PENDING_CHARGE = 5
STATE_PENDING_DISCHARGE = 6

class BatteryBar:
	def __init__(self):
		self.window = gtk.Window(gtk.WINDOW_POPUP)

		self.screen = self.window.get_screen()
		self.window.set_app_paintable(True)

		self.window.set_decorated(False)
		self.window.set_keep_above(True)
		self.window.set_accept_focus(False)
		self.window.set_skip_taskbar_hint(True)
		self.window.set_skip_pager_hint(True)
		self.window.stick()

		self.screen.connect("size-changed", self.screen_size_changed)
		self.window.connect("delete_event", self.delete_event)
		self.window.connect("destroy", self.destroy)
		self.window.connect("expose-event", self.expose)

		self.last_update = int(time.time())
		
		dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
		self.bus = dbus.SystemBus()
		self.battery = self.bus.get_object(UPOWER_BUSNAME, UPOWER_BATTERY_OBJECT)
		self.bus.add_signal_receiver(self.on_battery_changed, 'Changed', UPOWER_DEVICE_IFACE)
		self.on_battery_changed()
		
		self.set_size(self.screen.get_width(), 1)
		self.color = (0, 0, 0);

		gobject.timeout_add(60 * 1000, self.on_battery_changed)
		self.update()

		self.window.show()

	def loop(self):
		self.update()
		return True

	def update(self):
		self.color = self.compute_color()
		self.set_size(self.compute_width(), self.compute_height())

		self.window.queue_draw()

		current_time = int(time.time())
		if current_time > self.last_update + 150:
			self.last_update = current_time
			if self.battery_level < 0.2 and self.battery_state == STATE_DISCHARGING:
				gobject.timeout_add(25, self.flash)

	def flash(self):
		try:
			self.flash_count += 1
		except AttributeError:
			self.flash_count = 0

		flash_interval = 20.0
		limit = flash_interval * 8.0
		trans = flash_interval

		t = 1 - abs((self.flash_count % flash_interval) - flash_interval/2.0) * 2.0 / flash_interval
		t = t * t
		wt = max(0, min(self.flash_count / trans, (limit - self.flash_count) / trans, 1))

		r,g,b = self.compute_color()
		w,h = (self.compute_width(), self.compute_height())

		self.set_size(int(w * (1 - wt) + self.screen.get_width() * wt), h if wt < 1 else int(h + t * 10))
		self.color = tuple(map(lambda x, y: x * (1 - t) + y * t, (r,g,b), (1,0,0)))

		if self.flash_count < limit:
			return True
		else:
			self.flash_count = 0
			self.color = self.compute_color()
			self.set_size(w, h)
			return False

	def on_battery_changed(self):
		try:
			self.battery_level = self.battery.Get(UPOWER_BUSNAME, 'Percentage', dbus_interface=dbus.PROPERTIES_IFACE)/100
			self.battery_state = self.battery.Get(UPOWER_BUSNAME, 'State', dbus_interface=dbus.PROPERTIES_IFACE)
			print "Battery: " + str(self.battery_level) + " " + str(self.battery_state)
		except Exception as e:
			print e
		self.update()
		return True

	def compute_color(self):
		if self.battery_state == STATE_CHARGING:
			r = 0.2
			g = 0.6
			b = 1
		elif self.battery_state == STATE_FULLY_CHARGED:
			r = 0.2
			g = 1
			b = 1
		else:
			r = min(max(0.4, (0.75 - self.battery_level) * 4), 1)
			g = min(max(0, (self.battery_level - 0.2) * 5), 1)
			b = 0
		return (r, g, b)

	def compute_width(self):
		return int(1 + (self.screen.get_width() - 1) * self.battery_level)

	def compute_height(self):
		if self.battery_state == STATE_DISCHARGING:
			return int(min(max(2, math.ceil((0.5 - self.battery_level)/0.5 * 2)), 3))
		elif self.battery_state == STATE_FULLY_CHARGED:
			return 3
		else:
			return 2

	def set_size(self, width, height):
		self.window.move(0, self.screen.get_height() - height)
		self.window.resize(width, height)

	def screen_size_changed(self, screen, data=None):
		self.set_size(self.compute_width(), self.compute_height())

	def delete_event(self, widget, event, data=None):
		return False

	def destroy(self, widget, data=None):
		gtk.main_quit()

	def expose(self, widget, event, data=None):
		# Make window click-through
		size=self.window.window.get_size()
		bitmap=gtk.gdk.Pixmap(self.window.window,size[0],size[1],1)

		cr = bitmap.cairo_create()
		cr.set_operator(cairo.OPERATOR_SOURCE)
		cr.set_source_rgba(0.0, 0.0, 0.0, 0.0)
		cr.rectangle((0,0)+size)
		cr.fill()  

		self.window.input_shape_combine_mask(bitmap,0,0)

		# Set color
		dark = tuple(x * 0.6 for x in self.color)
		cr = self.window.get_window().cairo_create()
		cr.set_operator(cairo.OPERATOR_SOURCE)
		cr.set_source_rgba(*self.color)
		cr.rectangle((0,0)+size)
		cr.fill()
		cr.set_source_rgba(*dark)
		cr.rectangle((0,0,size[0],1))
		cr.fill()

		return False

if __name__ == "__main__":
	bat_bar = BatteryBar()
	gtk.main()

