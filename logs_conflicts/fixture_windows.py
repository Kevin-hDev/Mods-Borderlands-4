# Copyright (c) 2026 kevin-hDev
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Fakes of windows.py for the routes and service tests: record what would be copied or opened."""


class FakeWindows:
    def __init__(self, copy_result=(True, 1, "done"), folder_result="opened"):
        self.copy_result, self.folder_result = copy_result, folder_result
        self.copied, self.opened = [], []

    def set_clipboard(self, _api, text, _retries):
        self.copied.append(text)
        return self.copy_result

    def open_folder(self, folder):
        self.opened.append(folder)
        return self.folder_result


class FakeApi:
    @staticmethod
    def last_error():
        return 5
