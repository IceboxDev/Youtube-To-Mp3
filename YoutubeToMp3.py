#!/usr/bin/env python3

"""Youtube To MP3 Converter

Usage:
    YoutubeToMp3.py <Name> [-c][-s][-v][-b][-n][-p] [--sub=<s>] [--path=<p>] [--Vf=<vf>] [--Af=<af>]
    YoutubeToMp3.py (-h | --help)
    YoutubeToMp3.py --version

Options:
    Name           : i.e. "Rick Asley - Never Gonna Give You Up"
    --path=<p>     : Download path       [default: /home/%s/Music]
    --sub=<s>      : Subfolder inside the path
    --Vf=<vf>      : Format of the video [default: mp4]
    --Af=<af>      : Format of the audio [default: mp3]
    -c, --choice   : Allow user to choose a song himself
    -s, --silent   : Downloads everything silently
    -v, --video    : Download only the video file
    -b, --both     : Keep both, video and audio files
    -n, --name     : Keep the name, that has been specified
    -p, --play     : Play the song/video after downloading it
    -h, --help     : Show this screen.
    --version      : Show version.

"""

from pydub  import AudioSegment
from pytube import YouTube
from docopt import docopt

import subprocess
import termcolor
import requests
import getpass
import html
import re
import os

def line(color = "red"):
    
    output = str(subprocess.check_output(["tput", "cols"]))
    number = int(output.lstrip("b'").rstrip("\\n'"))
    
    termcolor.cprint("-" * number, color)

def text(text, index, color = "green", bold = 0, end = "\n"):

    if index:
        termcolor.cprint("%s." %str(index), "cyan" , attrs=["bold"] , end = "" )
    else:
        termcolor.cprint("  "             , "cyan" , attrs=["bold"] , end = "" )

    termcolor.cprint("| "                 , "red"                   , end = "" )

    if bold == "A":
        termcolor.cprint(text             , color  , attrs=["bold"] , end = end)

    elif bold:
        termcolor.cprint(text[:bold]      , color  , attrs=["bold"] , end = "" )
        termcolor.cprint(text[bold:]      , color                   , end = end)

    else:
        termcolor.cprint(text             , color                   , end = end)

#Given a youtube link, it downloads the video
def download_video(link, name, path="/home/icebox/Music", file_type="mp4"):
    yt = YouTube(link)
    
    yt.set_filename(name)

    regex   = r"\d{3,4}p"
    quality = str(yt.filter(file_type)[-1])
    match   = re.search(regex, quality)
    res     = match.group(0)

    video = yt.get(file_type, res)

    if display:
        message = "Downloading video in .%s format and %s resolution" %(file_type, res)
        text(message, 3 + choosing)
    
    if os.path.isdir(path):
        try:
            if subfolder:
                full_path = "%s/%s" %(path, subfolder)

                if not os.path.isdir(full_path):
                    os.makedirs(full_path)

                video.download(full_path)

            else:
                video.download(path)

        except OSError:
            if display:
                message = "Error: A file with this name already exists"
                text(message, 4 + choosing, color="red", bold="A")
                line()

            else:
                termcolor.cprint("Error: A file with this name already exists", "red")

            exit()

    else:
        if display:
            message = "Error: The given directory does not exist"
            text(message, 4 + choosing, color="red", bold="A")
            line()

        else:
            termcolor.cprint("Error: The given directory does not exist")
        
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
   
    invalid_links = []
    for index in range(len(links)):
        if "channel" in links[index] or \
           "user"    in links[index]:
            invalid_links.append(index)

    for index in invalid_links[::-1]:
        del names[index]
        del links[index]

    if choice and display:
        message = "Multiple matching videos found:"
        text(message, 2)

        for index, sname in enumerate(names):
            song_index = "[%s] " %(" "*(index+1 < 10) + str(index+1))
            song_name  = html.unescape(sname)
            message = song_index + song_name

            text(message, None, bold=4)

        while True:
            message = "     Which song would you like to download"
            text(message, None, end = " ")
            index = input()

            try:
                index = int(index)
                assert (0 < index <= 20)
                break

            except AssertionError:
                text("That is not a valid number!", None)

            except ValueError:
                text("That is not a number!", None)

        index -= 1

        
        if override:
            name = names[index]

        message = "Selected %s" %html.unescape(names[index])
        text(message, 3)

        return (DOWNLOAD %links[index], name)

    else:
        if override:
            name = names[0]

        if display:
            message = "Matching video found: '%s'" %html.unescape(names[0])
            text(message, 2)

        return (DOWNLOAD %links[0], name)

#Converts the video file to mp3
def video_to_mp3(path, file_type, audio_format="mp3", keep_both=False):

    if subfolder:
        plist = path.split("/")
        dire  = "/".join(plist[:-1])
        path  = "%s/%s/%s" %(dire, subfolder, plist[-1])

    AudioSegment.from_file(path).export(path.rstrip("."+file_type), format=audio_format)

    if not keep_both:
        os.remove(path)

#Main function
def get(name, convert = True):

    if display:
        message = "Finding matching video for '%s'" %name

        line()
        text(message, 1)

    values = find_video_link(name, choice = choosing, override = name_keep)
    video  = download_video(*values, path = dl_path, file_type = VideoF)

    P, F, E   = video
    full_path = "%s/%s.%s" %(P, F, E)

    if convert == True:

        if display:
            message = "Converting the file to .mp3 format"
            text(message, 4 + choosing)

        video_to_mp3(full_path, E, audio_format = AudioF, keep_both = both_files)
    
        if display:
            text("Done!", 5 + choosing, bold = "A")
            line()
        
        if autoplay:
            os.system("xdg-open '%s'" %full_path.rstrip(".%s" %E))

    else:
        if autoplay:
            os.system("xdg-open '%s'" %full_path)

        if display:
            text("Done!", 4 + choosing, bold = "A")
            line()

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
    global subfolder
    global autoplay

    if docopt_args["<Name>"]:

        display    = docopt_args["--silent"]
        both_files = docopt_args["--both"  ]
        video_only = docopt_args["--video" ]
        name_keep  = docopt_args["--name"  ]
        choosing   = docopt_args["--choice"]
        autoplay   = docopt_args["--play"  ]
        dl_path    = docopt_args["--path"  ]
        subfolder  = docopt_args["--sub"   ]
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

    user = getpass.getuser()
    arguments = docopt(__doc__ %user, version="YoutubeToMp3 Converter 1.5")
    
    main(arguments)

