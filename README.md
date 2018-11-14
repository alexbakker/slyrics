# slyrics

__slyrics__ is an external lyrics addon for Spotify.

![](https://alexbakker.me/u/ud8f2b5y.png)

It uses Spotify's undocumented local HTTP API to retrieve info about the track
that is currently playing. You can learn more about this API by reading [Carl
Byström's blog
post](http://cgbystrom.com/articles/deconstructing-spotifys-builtin-http-server/).
It then scrapes various websites to find lyrics and displays it to the user.

The goal is to be similar to
[Lyricfier](https://github.com/emilioastarita/lyricfier/) in terms of
functionality. The main difference is the fact that slyrics uses GTK for its
GUI, while Lyricfier uses electron. The functionality of this application is far
too simple to be able to justify running a separate instance of Chromium for it.

Currently, only Linux is supported. It shouldn't be too hard to port this to other
operating systems, but it is not considered a priority.
