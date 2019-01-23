from bs4 import BeautifulSoup
import requests
import regex


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


# words which might make finding a track's lyrics harder
FILTER_WORDS = ['explicit', 'bonus track', 'extra', 'album', 'version', 'remaster', 'soundtrack', 'radio', 'mix',
                'remix', 'original', 'edition', 'edit']


def filter_track(track, remove_encapsulated_texts=False, remove_filter_words=False, clean=False):
    """This function returns the track name as a string. Removes words, and  which might impede finding the lyrics.
    :type remove_encapsulated_texts: bool
        When remove_encapsulated_texts is True an aggressive regex is used which removes encapsulated substrings
    """
    track = track.lower()  # use lowered letters

    if remove_encapsulated_texts:
        # this regex replaces text encapsulated by: () [] '' {} <>
        # the exce
        # text is defined as: [\w0-9 !@#$%^&*\-_=+,.;:~]+
        for opening, closing in [['\\(', '\\)'], ['\\[', '\\]'], ["'", "'"], ['"', '"'], ['{', '}'], ['<', '>']]:
            track = regex.sub('(' + opening + r"[\w0-9 !@#$%^&*\-_=\+,.;:~]+" + closing + ')+', " ", track)

    # remove filter words which are surrounded by whitespace
    if remove_filter_words:
        track = regex.sub(r"((?:\s|^)" + "|".join(FILTER_WORDS) + r"(?:\s|$))", " ", track)

    # remove all characters which aren't 'a..z' or spaces
    if clean:
        track = regex.sub("[\W ]+", " ", track)

    return track.strip()


scrapers = [
    MusixmatchScraper(),
    GeniusScraper()
]

# the order in which different filter parameters are most likely to result in the wanted track string
FILTERS = [{'remove_encapsulated_texts': False, 'remove_filter_words': False, 'clean': False},
           {'remove_encapsulated_texts': False, 'remove_filter_words': False, 'clean': True},
           {'remove_encapsulated_texts': False, 'remove_filter_words': True, 'clean': True},
           {'remove_encapsulated_texts': True, 'remove_filter_words': True, 'clean': True}
           ]


def find(track, artist):
    for filter_kwargs in FILTERS:
        for scraper in scrapers:
            try:
                filtered_track = filter_track(track, **filter_kwargs)
            except Exception as e:
                filtered_track = track

            try:
                return scraper.find(filtered_track, artist)
            except Exception as e:
                continue
    return None
