import os
import json
import eyed3
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from collections import defaultdict


spotify = None


def function_call_counter(func):
    def wrapper(*args, **kwargs):
        wrapper.calls += 1
        return func(*args, **kwargs)
    wrapper.calls = 0
    return wrapper


def levenshtein_distance(str1, str2):
    def recursive(i, j):
        if i == 0 or j == 0:
            max(i, j)
        elif str1[i - 1] == str2[j - 1]:
            return recursive(i - 1, j - 1)
        else:
            return 1 + min(
                recursive(i, j - 1),
                recursive(i - 1, j),
                recursive(i - 1, j - 1)
            )

    return recursive(len(str1), str2)


def deduplicate_dict_keys(dictionary: dict):
    ddp_dict = dictionary.copy()
    for key in list(ddp_dict.keys()):
        try:
            new_key = spotify.search(key, limit=1, type="artist")['artists']['items'][0]['name']
        except IndexError:
            continue
        if key != new_key and new_key in list(ddp_dict.keys()):
            ddp_dict[new_key] += ddp_dict.pop(key)
        else:
            ddp_dict[new_key] = ddp_dict.pop(key)
    return


def init_user_tags(song, path_to_song):
    print("This song hasn't tags: " + path_to_song)
    song.initTag()
    song.tag.title = input("Input song name")
    song.tag.artist = input("Input song artist")
    song.tag.save()


def merge_dicts_with_list_values(dict1, dict2):
    for key, value in dict2.items():
        if key in dict1:
            dict1[key] += value
        else:
            dict1[key] = value


def load_songs(path: str):
    print("Load songs from " + path)
    songs = defaultdict(list)
    not_found_songs = defaultdict(list)

    for element in os.listdir(path):
        path_to_el = path + '\\' + element
        if os.path.isdir(path_to_el):
            load = load_songs(path_to_el)

            merge_dicts_with_list_values(songs, load[0])
            merge_dicts_with_list_values(not_found_songs, load[1])

        elif path_to_el[len(path_to_el) - 4:] == ".mp3":
            # processed = [song_artist, song_title, is_found [, song_id]]
            processed = process_song(path_to_el)
            print("Number of processed song: {0}".format(process_song.calls), end='\r')
            if processed[2]:
                songs[processed[0]].append([processed[1], processed[3]])
            else:
                not_found_songs[processed[0]].append(processed[1])

    return songs, not_found_songs


@function_call_counter
def process_song(path_to_song):
    song = eyed3.load(path_to_song)

    if song.tag is None:
        init_user_tags(song, path_to_song)
    if song.tag.artist is None:
        song.tag.artist = input("This song doesn't have artist: " + '\n'
                                + "Path to song: " + path_to_song + '\n'
                                + "Input the song artist: ")
        song.tag.save()
    if song.tag.title is None:
        song.tag.title = input("This song doesn't have title: " + path_to_song + '\n'
                               + "Input the song title: ")
        song.tag.save()

    song_title = song.tag.title
    song_artist = song.tag.artist

    search = spotify.search(q=song_title + " " + song_artist, type="track", limit=1)

    # third parameter in return is is_found
    try:
        return [song_artist, song_title, True, search['tracks']['items'][0]['id']]
    except IndexError:
        return [song_artist, song_title, False]


def authorization(user_name: str):
    scopes = "playlist-read-private playlist-modify-private"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(username=user_name, scope=scopes))
    return sp


def get_playlist_id_by_name(name):
    playlists = spotify.current_user_playlists()['items']
    for playlist in playlists:
        if playlist['name'] == name:
            return playlist['id']


def write_object_to_file(obj, name_of_file: str):
    songs_str = json.dumps(obj, indent=4)
    with open(os.path.join(os.environ['USERPROFILE'], 'Desktop', name_of_file), "w") as f:
        f.write(songs_str)
    print("The file with the songs not found is located on the Desktop in " + name_of_file)


def main():
    eyed3.log.setLevel("ERROR")

    user_name = input("Input your Spotify id (Username in Account overview): ")
    global spotify
    spotify = authorization(user_name)

    path = input("Input path to folder with songs: ")

    f_songs, nf_songs = load_songs(path)

    deduplicate_dict_keys(nf_songs)
    write_object_to_file(nf_songs, 'not_found_songs.json')

    playlist_name = input("Input playlist name: ")
    spotify.user_playlist_create(spotify.current_user()['id'], playlist_name)
    playlist_id = get_playlist_id_by_name(playlist_name)

    for artist, songs in f_songs.items():
        ids = []
        print("Add " + artist + " songs", end="\r")
        for song_info in songs:
            ids.append(song_info[1])
        spotify.user_playlist_add_tracks(spotify.current_user()['id'], playlist_id, ids)
#    with open("found_songs.json") as f:
#        f_songs = json.loads(f.read())
#        deduplicate_dict_keys(f_songs)
#        for artist, songs in f_songs.items():
#            ids = []
#            for songs_info in songs:
#                ids.append(songs_info[1])
#            # spotify.user_playlist_add_tracks("bf84829oudr7cxyd0nhhaat5v", "14BCJHKkF2HCISQZjMaHoV", ids)
#            spotify.user_playlist_add_tracks("iaao0jk0j2ezpyuucvp83vd9j", "14BCJHKkF2HCISQZjMaHoV", ids)


# spotify = authorization("iaao0jk0j2ezpyuucvp83vd9j")

if __name__ == '__main__':
    main()
