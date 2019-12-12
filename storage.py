import json


class Usernames:
    def __init__(self, file_path='usernames.json', autosave=True):
        self._file_path = file_path
        self._autosave = autosave

        self._usernames = list()
        self._last_checked_username_index = -1

        self._load()

    @property
    def list(self):
        return self._usernames

    def _load(self):
        try:
            with open(self._file_path, 'rb') as f:
                self._usernames = json.load(f)
        except FileNotFoundError:
            self._usernames = list()

    def next_username(self):
        next_i = self._last_checked_username_index + 1

        if next_i >= len(self._usernames):
            self._last_checked_username_index = 0
        else:
            self._last_checked_username_index = next_i

        return self._usernames[self._last_checked_username_index]

    def save(self):
        with open(self._file_path, 'w+') as f:
            json.dump(self._usernames, f, indent=4)

    @staticmethod
    def _normalize_username(username):
        username = username.lower()
        if username.startswith('@'):
            username = username.replace('@', '')

        return username

    def add(self, username, save=False):
        username = self._normalize_username(username)

        if username in self._usernames:
            return False

        self._usernames.append(username)

        if save or self._autosave:
            self.save()

        return True

    def remove(self, username, save=False):
        username = self._normalize_username(username)

        if username not in self._usernames:
            return False

        self._usernames = [u for u in self._usernames if u != username]

        if save or self._autosave:
            self.save()

        return True
