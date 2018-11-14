from slyrics.scrapers import scrapers
from slyrics.util import get_data_filename

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GLib
from gi.repository import Gtk

class SlyricsUI:
    def __init__(self):
        builder = Gtk.Builder()
        builder.add_from_file(get_data_filename("assets/ui.glade"))
        builder.connect_signals(self)

        self._window = builder.get_object("window_main")
        self._box_loading = builder.get_object("box_loading")
        self._box_main = builder.get_object("box_main")
        self._label_song = builder.get_object("label_song")
        self._label_lyrics = builder.get_object("label_lyrics")
        self._link_lyrics = builder.get_object("link_lyrics")
        self._combo_sources = builder.get_object("combo_sources")
        self._store_sources = builder.get_object("store_sources")

        for scraper in scrapers:
            self._store_sources.insert(-1, [scraper.name])
        self._combo_sources.set_active(0)

        self._window.add(self._box_loading)

    def start(self):
        self._window.show_all()
        Gtk.main()

    def stop(self):
        Gtk.main_quit()

    def update_connection_status(self, connected):
        self._window.remove(self._window.get_children()[0])
        if connected:
            self._window.add(self._box_main)
        else:
            self._window.set_title("Slyrics (disconnected)")
            self._window.add(self._box_loading)

    def update_status(self, status):
        version = status.get_version()
        title = "Slyrics (connected to Spotify{0})".format("" if version is None else " " + version)
        self._label_song.set_text(status.get_track_string())
        self._window.set_title(title)
        self._label_lyrics.set_text("")
        self._link_lyrics.hide()
        self._combo_sources.hide()

    def update_lyrics(self, lyrics):
        if not lyrics:
            self._link_lyrics.set_uri("")
            self._link_lyrics.hide()
            self._combo_sources.hide()
            text = "Couldn't find lyrics."
        else:
            self._link_lyrics.set_uri(lyrics.get_url())
            self._link_lyrics.show()
            self._combo_sources.show()
            text = lyrics.get_text()
        self._label_lyrics.set_text(text)

    def on_connection_status_change(self, connected):
        GLib.idle_add(self.update_connection_status, connected)

    def on_status_change(self, status):
        GLib.idle_add(self.update_status, status)

    def on_lyrics_change(self, lyrics):
        GLib.idle_add(self.update_lyrics, lyrics)

    def on_delete(self, *args):
        Gtk.main_quit(*args)
