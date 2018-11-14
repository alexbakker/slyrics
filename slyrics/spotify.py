from datetime import timedelta

import requests
import dbus


class SpotifyWebStatus:
    def __init__(self, status):
        self._status = status

    def get_track_string(self):
        return "{0} - {1}".format(self.get_track_name(), self.get_track_artist())

    def get_track_name(self):
        return self._status["track"]["track_resource"]["name"]

    def get_track_artist(self):
        return self._status["track"]["artist_resource"]["name"]

    def get_version(self):
        return self._status["client_version"]

    def __eq__(self, other):
        return (other and
                self.get_track_name() == other.get_track_name() and
                self.get_track_artist() == other.get_track_artist())

    def __ne__(self, other):
        return not self.__eq__(other)


class SpotifyBusStatus:
    def __init__(self, status):
        self._status = status

    def get_track_string(self):
        return "{0} - {1}".format(self.get_track_name(), self.get_track_artist())

    def get_track_position(self):
        microtime = self._status.get('mpris:length')
        return str(timedelta(microseconds=microtime))[:-7]

    def get_track_name(self):
        return self._status.get('xesam:title')

    def get_track_artist(self):
        return self._status.get('xesam:artist')[0]

    def get_version(self):
        return None

    def __eq__(self, other):
        return (other and
                self.get_track_name() == other.get_track_name() and
                self.get_track_artist() == other.get_track_artist())

    def __ne__(self, other):
        return not self.__eq__(other)


class spotifyClient:
    """Abstract class which defines the Spotify interface"""

    def find(self):
        raise NotImplementedError("This method has not been implemented!")

    def get_status(self):
        raise NotImplementedError("This method has not been implemented!")


class SpotifyWebClient(spotifyClient):
    _ports = (4380, 4389)

    def __init__(self, host="localhost", port=None):
        self._host = host
        self._port = port
        self._oauth = None
        self._csrf = None

    def _req_raw(self, url, **kwargs):
        return requests.request("GET", url, verify=True, **kwargs).json()

    def _req(self, path, params=None, auth=True, spoof=True, **kwargs):
        url = self._get_url(path)

        headers = {}
        if spoof:
            headers["Origin"] = "https://open.spotify.com"

        if not params:
            params = {}

        if auth:
            if not self._oauth or not self._csrf:
                raise Exception("tokens are null, call find() first")
            params["oauth"] = self._oauth
            params["csrf"] = self._csrf

        return self._req_raw(url, headers=headers, params=params, **kwargs)

    def _get_url(self, path):
        return "http://{0}:{1}{2}".format(self._host, self._port, path)

    def _get_field(self, res, name):
        if not name in res:
            raise Exception("bad response")
        return res[name]

    def _get_oauth(self):
        return self._get_field(self._req_raw("http://open.spotify.com/token"), "t")

    def _get_csrf(self):
        return self._get_field(self._req("/simplecsrf/token.json", auth=False), "token")

    # todo: add verbose param
    def find(self):
        self._oauth = self._get_oauth()

        for i in range(self._ports[0], self._ports[1]):
            self._port = i
            try:
                self._csrf = self._get_csrf()
            except Exception as e:
                continue
            return

        self._port = None
        raise Exception("unable to find Spotify")

    def get_port(self):
        return self._port

    def get_status(self):
        res = self._req("/remote/status.json")
        if "error" in res:
            raise Exception("api error {0}: {1}".format(res["error"]["type"], res["error"]["message"]))
        if not "track" in res:
            raise Exception("no track info in status response")
        return SpotifyWebStatus(res)


class SpotifyBusClient(spotifyClient):
    def find(self):
        bus = dbus.SessionBus()
        self._bus = bus.get_object('org.mpris.MediaPlayer2.spotify', '/org/mpris/MediaPlayer2')
        self.player = dbus.Interface(self._bus, 'org.freedesktop.DBus.Properties')

    def get_status(self):
        res = self.player.Get('org.mpris.MediaPlayer2.Player', 'Metadata')
        return SpotifyBusStatus(res)
