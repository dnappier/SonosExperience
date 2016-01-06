import pylast

class AlbumManager(object):
    '''
    Manages album art extraction and the logic behind a pic in failure
    '''

    def __init__(self, key, shared_secret, username, password):
        self.album_art = ''
        password_hash = pylast.md5(password)
        self.network = pylast.LastFMNetwork(api_key=key,
                                            api_secret=shared_secret,
                                            username=username,
                                            password_hash=password_hash)

    def get_album_image(self, **kwargs):
        title = ''
        if 'album_art' in kwargs.keys() and len(kwargs['album_art']) > 0:
            self.album_image = kwargs['album_art']
            return kwargs['album_art']

        if 'title' in kwargs.keys():
            if ' (' in kwargs['title']:
                # this is usually a featuring, which lastfm doesn't like
                # so we strip off from that space to the end of the string
                title = kwargs['title'][:kwargs['title'].index(' (')]
            else:
                title = kwargs['title']
        else:
            return None

        # get the album information for this track
        album = pylast.Album(kwargs['artist'], title, self.network)
        try:
            coverImage = album.get_cover_image()
            self.album_art = coverImage
            return coverImage
        except pylast.WSError:
            coverImage = None
            print("AlbumManager: can't find album details for %(title)s by %(artist)s from lastfm" % kwargs)
        except:
            # usually this is an add in our music stream
            print('AlbumManager: unknown lastfm failure')
            print(track)
            traceback.print_exc()

        artist = self.network.get_artist(kwargs['artist'])
        # [[pylast.album, 125356], [album, ...]]
        album_list = artist.get_top_albums()

        #search for the right album title
        for album in album_list:
            if str(album[0].title).lower() in str(kwargs['album']).lower():
                print ("AlbumManager: found album %s from the info given" % album[0].title)
                self.album_art = album.get_cover_image()
                return self.album_art

        if len(album_list) > 0:
            print('AlbumManager: unable to find a matching album cover, using %s'
                  % album_list[0][0].title)
            self.album_art = album_list[0][0].get_cover_image()
            return self.album_art

        # if we still can't find it then just get a picture of the artist
        artist = network.get_artist(artist)
        self.album_art = artist.get_cover_image()

        return self.album_art

    def get_album_image_format(self):
        return self.album_art[self.album_art[-5:].index('.'):]

