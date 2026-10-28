# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Runs the mod's start on the game's thread, from the mod's load, which runs on a thread of its own (verified in
game: Characters, trial 207, borderlands_4/mods/perso/characters/source/characters/game_thread.py). The game-thread
queue (game_thread.py) must be created on the game's thread, or the game never hands it a message.

Unreal runs its game loop on the process's main thread, the first one Windows created (verified in game on 26 October
2026: the queue made there ran every change of the page). A one-shot message hook of that thread (WH_GETMESSAGE) runs
our task there when the thread next reads a message; we post it an empty one so that happens at its next frame,
paused or not. The hook removes itself at that first call: afterwards nothing of ours runs per message (OPTI.md,
rule 1)."""

import ctypes
import os
import threading
from ctypes import wintypes

TH32CS_SNAPTHREAD = 0x00000004
THREAD_QUERY_LIMITED_INFORMATION = 0x0800
WH_GETMESSAGE = 3
WM_NULL = 0x0000
INVALID_HANDLE = ctypes.c_void_p(-1).value
LRESULT = ctypes.c_ssize_t
HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)


class THREADENTRY32(ctypes.Structure):
    _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD), ("th32ThreadID", wintypes.DWORD),
                ("th32OwnerProcessID", wintypes.DWORD), ("tpBasePri", ctypes.c_long),
                ("tpDeltaPri", ctypes.c_long), ("dwFlags", wintypes.DWORD)]


def windows_api():
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel32.Thread32First.argtypes = [wintypes.HANDLE, ctypes.POINTER(THREADENTRY32)]
    kernel32.Thread32Next.argtypes = [wintypes.HANDLE, ctypes.POINTER(THREADENTRY32)]
    kernel32.OpenThread.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenThread.restype = wintypes.HANDLE
    kernel32.GetThreadTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.GetCurrentThreadId.restype = wintypes.DWORD
    user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]
    user32.SetWindowsHookExW.restype = wintypes.HHOOK
    user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
    user32.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
    user32.CallNextHookEx.restype = LRESULT
    user32.PostThreadMessageW.argtypes = [wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    return user32, kernel32


def created_at(kernel32, thread_id: int):
    handle = kernel32.OpenThread(THREAD_QUERY_LIMITED_INFORMATION, False, thread_id)
    if not handle:
        return None
    try:
        times = [wintypes.FILETIME() for _ in range(4)]
        if not kernel32.GetThreadTimes(handle, *[ctypes.byref(item) for item in times]):
            return None
        return (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime
    finally:
        kernel32.CloseHandle(handle)


def main_thread_id(api=None) -> int:
    """The id of this process's first thread. Raises OSError when Windows cannot list them."""
    _user32, kernel32 = api or windows_api()
    snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0)
    if not snapshot or snapshot == INVALID_HANDLE:
        raise OSError(ctypes.get_last_error(), "CreateToolhelp32Snapshot refused")
    pid, oldest = os.getpid(), None
    try:
        entry = THREADENTRY32(dwSize=ctypes.sizeof(THREADENTRY32))
        more = kernel32.Thread32First(snapshot, ctypes.byref(entry))
        while more:
            if entry.th32OwnerProcessID == pid:
                when = created_at(kernel32, entry.th32ThreadID)
                if when is not None and (oldest is None or when < oldest[0]):
                    oldest = (when, entry.th32ThreadID)
            more = kernel32.Thread32Next(snapshot, ctypes.byref(entry))
    finally:
        kernel32.CloseHandle(snapshot)
    if oldest is None:
        raise OSError(0, "no thread of this process could be read")
    return oldest[1]


class OnThread:
    """Runs task once on thread_id, at the next message that thread reads. on_error gets the error's type name: a
    Python error must never cross back into the game's message loop. on_timeout runs, on a thread of ours, when the
    task has not run within timeout_s; the hook is then removed.

    The hook is set by a thread of ours that stays alive until the hook has run, is cancelled or times out: Windows
    removes a hook when the thread that set it ends, and the SDK's load thread ends right after the last mod is
    imported (review of 26 October 2026; pyunrealsdk: "this thread gets destroyed"). Set from that thread, the start
    never ran when Mod Settings was the last mod loaded."""

    def __init__(self, thread_id: int, task, on_error, timeout_s: float, on_timeout, api=None):
        self.user32, self.kernel32 = api or windows_api()
        self.thread_id = thread_id
        self.task = task
        self.on_error = on_error
        self.timeout_s = timeout_s
        self.on_timeout = on_timeout
        self.lock = threading.Lock()
        self.done = False
        self.hook = None
        self.failure = None
        self.finished = threading.Event()
        set_or_refused = threading.Event()
        # Kept alive while the hook is set: Windows calls through this pointer.
        self.procedure = HOOKPROC(self.called)
        self.keeper = threading.Thread(target=self.keep, args=(set_or_refused,), name="mod-settings-start",
                                       daemon=True)
        self.keeper.start()
        set_or_refused.wait()
        if self.failure is not None:
            raise OSError(*self.failure)

    def keep(self, set_or_refused) -> None:
        try:
            hook = self.user32.SetWindowsHookExW(WH_GETMESSAGE, self.procedure, None, self.thread_id)
            if not hook:
                self.failure = (ctypes.get_last_error(), "SetWindowsHookExW refused")
                return
            with self.lock:
                self.hook = hook
                # The thread may have read a message between the two lines above: the hook then ran without it.
                ran_already = self.done
            if ran_already:
                self.cancel()
            elif not self.user32.PostThreadMessageW(self.thread_id, WM_NULL, 0, 0):
                self.failure = (ctypes.get_last_error(), "PostThreadMessageW refused")
                self.cancel()
                return
        finally:
            set_or_refused.set()
        if not self.finished.wait(self.timeout_s):
            # Decided and claimed at once: a hook running right now then finds the task taken and leaves it.
            with self.lock:
                missed = not self.done
                self.done = True
            self.cancel()
            if missed:
                self.on_timeout()

    def called(self, code, wparam, lparam):
        hook = self.hook
        if not self.done and self.kernel32.GetCurrentThreadId() == self.thread_id:
            with self.lock:
                first = not self.done
                self.done = True
            if first:
                self.cancel()
                try:
                    self.task()
                except BaseException as error:
                    self.on_error(type(error).__name__)
        return self.user32.CallNextHookEx(hook, code, wparam, lparam)

    def cancel(self) -> None:
        """Any thread: the hook is removed, the task will not run if it has not yet, the keeper thread ends."""
        with self.lock:
            hook, self.hook = self.hook, None
            self.done = True
        if hook:
            self.user32.UnhookWindowsHookEx(hook)
        self.finished.set()
