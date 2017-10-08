#!/usr/bin/env python3

"""Youtube To MP3 Converter

Usage:
    YoutubeToMp3.py <Name> [-c][-s][-v][-b][-n] [--Path=<p>] [--Vf=<vf>] [--Af=<af>]
    YoutubeToMp3.py (-h | --help)
    YoutubeToMp3.py --version

Options:
    Name           : i.e. "Rick Asley - Never Gonna Give You Up"
    --Path=<p>     : Download path       [default: /home/icebox/Music]
    --Vf=<vf>      : Format of the video [default: mp4]
    --Af=<af>      : Format of the audio [default: mp3]
    -c, --choice   : Allow user to choose a song himself
    -s, --silent   : Downloads everything silently
    -v, --video    : Download only the video file
    -b, --both     : Keep both, video and audio files
    -n, --name     : Keep the name, that has been specified
    -h, --help     : Show this screen.
    --version      : Show version.

"""

from pydub  import AudioSegment
from pytube import YouTube
from docopt import docopt

import termcolor
import requests
import html
import re
import os

#Given a youtube link, it downloads the video
#Renames the video file to name
#Prioritizes best quality
def download_video(link, name, path="/home/icebox/Music", file_type="mp4"):
    yt = YouTube(link)
    
    yt.set_filename(name)

    regex   = r"\d{3,4}p"
    quality = str(yt.filter(file_type)[-1])
    match   = re.search(regex, quality)
    res     = match.group(0)

    video = yt.get(file_type, res)

    if display:
        termcolor.cprint("3."         , "cyan" , attrs=["bold"] , end=""  )
        termcolor.cprint("|"          , "red"                   , end=""  )
        termcolor.cprint("Downloading video in .%s format and %s resolution" \
                    %(file_type, res) , "green"                 , end="\n")
    
    try:
        video.download(path)

    except OSError:
        if display:
            termcolor.cprint("4."         , "cyan" , attrs=["bold"] , end=""  )
            termcolor.cprint("|"          , "red"                   , end=""  )
            termcolor.cprint("Error: A file with this name already exists" \
                                          , "red"  , attrs=["bold"] , end="\n")
            termcolor.cprint("--+"+"-"*98 , "red"  , attrs=["bold"] , end="\n")

        else:
            termcolor.cprint("Error: A file with this name already exists", "red")

        exit()

    return (path, name, file_type)

#Finds relevant videos and their links
def find_video_link(name, choice = False, override = True):
    
    SEARCH   = "https://www.youtube.com/results?search_query=%s"
    DOWNLOAD = "https://www.youtube.com%s"

    r        = requests.get(SEARCH %name)
    source   = r.text
    
    names_regex = r'(?<=title=")(.*?)(?=" aria-describedby="description|" rel="spf-prefetch)'
    links_regex = r'(?<=href=")(.*?)(?=" class="yt-uix-tile-link)'

    names = re.findall(names_regex, source)
    links = re.findall(links_regex, source)

    names = names[len(names) == 21:]
    links = links[len(links) == 21:]
    
    if choice and display:
        termcolor.cprint("2."                               , "cyan", attrs=["bold"], end=""  )
        termcolor.cprint("|"                                , "red"                 , end=""  )
        termcolor.cprint("Multiple matching videos found:"  , "green"               , end="\n")

        for index, sname in enumerate(names):
            termcolor.cprint("  |"                , "red"   ,                 end=""  )
            termcolor.cprint("[%s] " %(" "*(index+1 < 10) + str(index+1))\
                                                  , "green" , attrs=["bold"], end=""  )
            termcolor.cprint(html.unescape(sname) , "green" ,                 end="\n")

        while True:
            termcolor.cprint("  |     "                                , "red"   , end="")
            termcolor.cprint("Which song would you like to download: " , "green" , end="")

            index = input()

            try:
                index = int(index)
                assert (0 < index <= 20)
                break

            except AssertionError:
                termcolor.cprint("  |     "                    , "red"   , end=""  )
                termcolor.cprint("That is not a valid number!" , "green" , end="\n")

            except ValueError:
                termcolor.cprint("  |     "                    , "red"   , end=""  )
                termcolor.cprint("That is not a number!"       , "green" , end="\n")

        index -= 1

        
        if override:
            name = names[index]

        termcolor.cprint("2."   , "cyan", attrs=["bold"], end=""  )
        termcolor.cprint("|"    , "red"                 , end=""  )
        termcolor.cprint("Matching video found: '%s'" \
        %html.unescape(names[index]), "green"               , end="\n")

        return (DOWNLOAD %links[index], name)

    else:
        if override:
            name = names[0]

        if display:
            termcolor.cprint("2."   , "cyan", attrs=["bold"], end=""  )
            termcolor.cprint("|"    , "red"                 , end=""  )
            termcolor.cprint("Matching video found: '%s'" \
            %html.unescape(names[0]), "green"               , end="\n")
        
        return (DOWNLOAD %links[0], name)

#Converts the video file to mp3
def video_to_mp3(path, file_type, audio_format="mp3", keep_both=False):

    AudioSegment.from_file(path).export(path.rstrip("."+file_type), format=audio_format)

    if not keep_both:
        os.remove(path)

#Main function
def get(name, convert = True):

    if display:
        termcolor.cprint("--+"+"-"*98 , "red" , attrs=["bold"], end="\n")
        termcolor.cprint("1."         , "cyan", attrs=["bold"], end=""  )
        termcolor.cprint("|"          , "red"                 , end=""  )
        termcolor.cprint("Finding matching video for '%s'" \
                                %name , "green"               , end="\n")

    values = find_video_link(name, choice = choosing, override = name_keep)
    video  = download_video(*values, path = dl_path, file_type = VideoF)

    if convert == True:

        if display:
            termcolor.cprint("4."                          , "cyan" , attrs=["bold"] , end=""  )
            termcolor.cprint("|"                           , "red"                   , end=""  )
            termcolor.cprint("Converting the file to .mp3" , "green"                 , end="\n")

        P, F, E   = video
        full_path = "%s/%s.%s" %(P, F, E)

        video_to_mp3(full_path, E, audio_format = AudioF, keep_both = both_files)
    
        if display:
            termcolor.cprint("5."         , "cyan" , attrs=["bold"] , end=""  )
            termcolor.cprint("|"          , "red"                   , end=""  )
            termcolor.cprint("Done!"      , "green", attrs=["bold"] , end="\n")
            termcolor.cprint("--+"+"-"*98 , "red"  , attrs=["bold"] , end="\n")

    elif display:
        termcolor.cprint("4."         , "cyan" , attrs=["bold"] , end=""  )
        termcolor.cprint("|"          , "red"                   , end=""  )
        termcolor.cprint("Done!"      , "green", attrs=["bold"] , end="\n")
        termcolor.cprint("--+"+"-"*98 , "red"  , attrs=["bold"] , end="\n")

#Main Docopt function
def main(docopt_args):
    global display
    global both_files
    global video_only
    global name_keep
    global choosing
    global VideoF
    global AudioF
    global dl_path

    if docopt_args["<Name>"]:

        display    = docopt_args["--silent"]
        both_files = docopt_args["--both"  ]
        video_only = docopt_args["--video" ]
        name_keep  = docopt_args["--name"  ]
        choosing   = docopt_args["--choice"]
        dl_path    = docopt_args["--Path"  ]
        VideoF     = docopt_args["--Vf"    ]
        AudioF     = docopt_args["--Af"    ]
        
        display    = not display
        name_keep  = not name_keep
        
        if choosing and not display:
            termcolor.cprint("Warning: Choice flag shouldn't be used together with Silent flag.   \
                              \nIgnoring Choice flag.", "red")

        if both_files and video_only:
            termcolor.cprint("Warning: Video flag shouldn't be used together with Both-File flag. \
                              \nIgnoring Video flag.",  "red")
        else:
            video_only = not video_only


        get(docopt_args["<Name>"], convert = video_only)
            
if __name__ == "__main__":

    arguments = docopt(__doc__, version="YoutubeToMp3 Converter 1.1")

    main(arguments)

