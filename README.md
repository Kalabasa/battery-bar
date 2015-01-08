battery bar
===========

Minimal battery bar in Python

Requirements
------------

* Python
* GTK
* Cairo
* UPower

Usage
-----

Edit the script to set the battery system path. Replace "BATA" in UPOWER_BATTERY_OBJECT by your battery's system path (usually "BAT0").

Then execute
```
./bbar.py
```

Use `bbar-timed.py` for a version that uses polling instead of listening to dbus notifications.
