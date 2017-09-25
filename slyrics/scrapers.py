from bs4 import BeautifulSoup
import requests

class Lyrics:
    def __init__(self, url, text):
        self._url = url
        self._text = text

    def get_url(self):
        return self._url

    def get_text(self):
        return self._text

class Scraper:
    def __init__(self, name):
        self.name = name

    def req(self, url, **kwargs):
        return requests.get(url, **kwargs)

    def find(self, track, artist):
        raise NotImplementedError("method not callable from base class")

class GeniusScraper(Scraper):
    def __init__(self):
        super().__init__("Genius")

    def find(self, track, artist):
        url = "https://genius.com/search?q={0} {1}".format(track, artist)
        res = self.req(url).text
        soup = BeautifulSoup(res, 'html.parser')
        url = soup.find("a", {"class": " song_link"}, href=True)
        if not url:
            raise Exception("couldn't find track")
        url = url["href"]

        res = self.req(url).text
        soup = BeautifulSoup(res, 'html.parser')
        lyrics = soup.find("div", {"class": "lyrics"})
        if not lyrics:
            raise Exception("error parsing lyrics")

        return Lyrics(url, lyrics.p.text)

class MusixmatchScraper(Scraper):
    def __init__(self):
        super().__init__("Musixmatch")

    def req(self, url, **kwargs):
        # yes, circumventing musixmatch's scraping prevention is really this easy
        return super().req(url, headers={"User-Agent": ""}, **kwargs)

    def find(self, track, artist):
        base_url = "https://www.musixmatch.com"
        url = "{0}/search/{1} {2}".format(base_url, track, artist)
        res = self.req(url).text
        soup = BeautifulSoup(res, 'html.parser')
        url = soup.find("h2", {"class": "media-card-title"}).a
        if not url:
            raise Exception("couldn't find track")
        url = base_url + url["href"]

        res = self.req(url).text
        soup = BeautifulSoup(res, 'html.parser')
        parts = soup.find_all("p", {"class": "mxm-lyrics__content"})
        if not parts:
            raise Exception("error parsing lyrics")

        lyrics = ""
        for part in parts:
            lyrics += part.text

        return Lyrics(url, lyrics)

def filter_track(track):
    """This function returns the track name as a string. Removes words, and  which might impede finding the lyricsm."""
    filtered_track = track
    for f in FILTERS:
        index = track.lower().find(f.lower())  # ignore case
        if index != -1:
            filtered_track = track[: index] + track[index + len(f):]
    return filtered_track if not filtered_track.endswith(" ") else filtered_track[-1]  # remove trailing white space

FILTERS = [" - (explicit)", " (explicit)"]  # todo: use/build filter strings  'smarter'

scrapers = [
    MusixmatchScraper(),
    GeniusScraper()
]

def find(track, artist):
    for scraper in scrapers:
        try:
            filtered_track = filter_track(track)
            return scraper.find(filtered_track, artist)
        except Exception as e:
            continue
    return None
