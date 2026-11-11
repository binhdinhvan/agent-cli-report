"""Raise/map only a window owned by the supplied PID on the private Xvfb display."""
import ctypes as c
import json
import sys

x = c.CDLL("libX11.so.6")
Window = c.c_ulong
Display = c.c_void_p
x.XOpenDisplay.argtypes = [c.c_char_p]
x.XOpenDisplay.restype = Display
x.XDefaultRootWindow.argtypes = [Display]
x.XDefaultRootWindow.restype = Window
x.XInternAtom.argtypes = [Display, c.c_char_p, c.c_int]
x.XInternAtom.restype = c.c_ulong
x.XQueryTree.argtypes = [Display, Window, c.POINTER(Window), c.POINTER(Window), c.POINTER(c.POINTER(Window)), c.POINTER(c.c_uint)]
x.XGetWindowProperty.argtypes = [Display, Window, c.c_ulong, c.c_long, c.c_long, c.c_int, c.c_ulong,
    c.POINTER(c.c_ulong), c.POINTER(c.c_int), c.POINTER(c.c_ulong), c.POINTER(c.c_ulong), c.POINTER(c.POINTER(c.c_ubyte))]
x.XMapRaised.argtypes = [Display, Window]
x.XRaiseWindow.argtypes = [Display, Window]
x.XSetInputFocus.argtypes = [Display, Window, c.c_int, c.c_ulong]
x.XSync.argtypes = [Display, c.c_int]
x.XFree.argtypes = [c.c_void_p]
x.XCloseDisplay.argtypes = [Display]
display = x.XOpenDisplay(b":91")
assert display, "Private X display unavailable"
root = x.XDefaultRootWindow(display)
atom = x.XInternAtom(display, b"_NET_WM_PID", 0)
target_pid = int(sys.argv[1])
found = None


def search(window, frame=None, depth=0):
    global found
    if depth > 8 or found:
        return
    typ, fmt, count, after = c.c_ulong(), c.c_int(), c.c_ulong(), c.c_ulong()
    data = c.POINTER(c.c_ubyte)()
    x.XGetWindowProperty(display, window, atom, 0, 1, 0, 0,
        c.byref(typ), c.byref(fmt), c.byref(count), c.byref(after), c.byref(data))
    if count.value and fmt.value == 32:
        pid = c.cast(data, c.POINTER(c.c_ulong))[0]
        if pid == target_pid:
            found = (window, frame or window)
    if data:
        x.XFree(data)
    r, parent, n = Window(), Window(), c.c_uint()
    children = c.POINTER(Window)()
    if x.XQueryTree(display, window, c.byref(r), c.byref(parent), c.byref(children), c.byref(n)):
        for i in range(n.value):
            search(children[i], children[i] if window == root else frame, depth + 1)
        if children:
            x.XFree(children)


try:
    search(root)
    assert found, "No native window matching the owned process PID"
    client, frame = found
    x.XMapRaised(display, frame)
    x.XMapRaised(display, client)
    x.XRaiseWindow(display, frame)
    x.XSync(display, 0)
    print(json.dumps({"owned_pid": target_pid, "client_window": int(client), "frame_window": int(frame),
                      "action": "map_raise_on_private_display; focus left to window manager"}))
finally:
    x.XCloseDisplay(display)
