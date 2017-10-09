#!/usr/bin/env python3

"""Youtube To MP3 Converter

Usage:
    Youtube <Name> [-c][-s][-v][-b][-n][-p] [--sub=<s>] [--path=<p>] [--Vf=<vf>] [--Af=<af>]
    Youtube --clip [-s][-v][-b][-p] [--sub=<s>] [--path=<p>] [--Vf=<vf>] [--Af=<af>]
    Youtube (-h | --help)
    Youtube --version

Options:
    Name                : i.e. "Rick Asley - Never Gonna Give You Up"
    --path=<p>          : Download path       [default: /home/%s/Music]
    --sub=<s>           : Subfolder inside the path
    --Vf=<vf>           : Format of the video [default: mp4]
    --Af=<af>           : Format of the audio [default: mp3]
    -c, --choice        : Allow user to choose a song himself
    -s, --silent        : Downloads everything silently
    -v, --video         : Download only the video file
    -b, --both          : Keep both, video and audio files
    -n, --name          : Keep the name, that has been specified
    -p, --play          : Play the song/video after downloading it
    -h, --help          : Show this screen.
    --clip              : Use the link from your clipboard
    --version           : Show version.

"""

#Imports
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

#Constants
VERSION = 2.0
USER    = getpass.getuser()
INDEX   = 1

###############################################################################
#Functions used for terminal output
###############################################################################

#Prints a colored line
def line(color = "red"):
    
    output = str(subprocess.check_output(["tput", "cols"]))
    number = int(output.lstrip("b'").rstrip("\\n'"))
    
    termcolor.cprint("-" * number, color)

#Prints colored text
def text(text, index, color = "green", bold = 0, end = "\n"):
    global INDEX

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
    
    if INDEX:
        INDEX += 1
    
###############################################################################
#Scraping functions
###############################################################################

#Youtube video link to it's name
def link_to_name(link):
    r       = requests.get(link)
    source  = r.text

    regex   = r'(?<=<meta itemprop="name" content=")(.*?)(?=">)'
    match   = re.search(regex, source)
    name    = match.group(0)

    return name

#Converts a video name to link(s)
def name_to_link(name):
    SEARCH   = "https://www.youtube.com/results?search_query=%s"
    r        = requests.get(SEARCH %name)
    source   = r.text
    
    names_regex = r'(?<=title=")(.*?)(?=" aria-describedby="description|" rel="spf-prefetch)'
    links_regex = r'(?<=href=")(.*?)(?=" class="yt-uix-tile-link)'

    names = re.findall(names_regex, source)
    links = re.findall(links_regex, source)
    
    return (names, links)

#Filters out unwanted links
def filtering(names, links, filt="watch"):
    #Filters: channel/user/watch
    
    names = names[len(names) == 21:]
    links = links[len(links) == 21:]
   
    invalid_links = []
    for index in range(len(links)):
        if filt not in links[index]:
            invalid_links.append(index)

    for index in invalid_links[::-1]:
        del names[index]
        del links[index]
    
    return (names, links)

###############################################################################
#Download and conversion functions
###############################################################################

#Given link, downloads youtube video
def download_video(link, name, path, video_format):
    yt = YouTube(link)
    yt.set_filename(name)
    
    regex   = r"\d{3,4}p"
    quality = str(yt.filter(video_format)[-1])
    match   = re.search(regex, quality)
    res     = match.group(0)

    video = yt.get(video_format, res)
    
    try:
        video.download(path)
        return True
        
    except OSError:
        return False

#Converts the video file to mp3
def video_to_mp3(path, target, audio_format):
    input_file  = "%s/%s"    %(path, target)
    output_file = "%s/%s.%s" %(path, target.split(".")[0], audio_format)
    
    AudioSegment.from_file(input_file).export(output_file, format=audio_format)
    
    return True

###############################################################################
#Tool Functions
###############################################################################

#Parse Docopt
def arguments():
    args = docopt(__doc__ %USER, version="YoutubeToMp3 Converter %s" %VERSION)
    
    if args["--choice"] and args["--silent"]:
        termcolor.cprint("Warning: Choice flag shouldn't be used together with Silent flag.    \
                          \nIgnoring Choice flag.", "red")

    if args["--video"]  and args["--both"  ]:
        termcolor.cprint("Warning: Video flag shouldn't be used together with Both-Files flag. \
                          \nIgnoring Video flag.",  "red")
                          
    return args

#Creates a valid path
def path(options, display):
    global INDEX
    
    path      = options["--path"]
    subfolder = options["--sub" ]
    
    if not os.path.isdir(path):
        if display:
            message = "Error: The given directory does not exist"
            text(message, INDEX, color="red", bold="A")
            line()

        else:
            termcolor.cprint("Error: The given directory does not exist")
        
        exit()
    
    if subfolder:
        full_path = "%s/%s" %(path, subfolder)
        
        if not os.path.isdir(full_path):
            if display:
                message = "Creating subdirectory %s" %subfolder
                text(message, INDEX, color="red", bold="A")
                
            os.makedirs(full_path)
        
        return full_path
    
    else:
        return path

#Handles failed downloads
def failed_download(file_path, target, display):
    global INDEX
    
    full_path = "%s/%s" %(file_path, target)
    
    if os.path.isfile(full_path):
        message = "Error: A file with this name already exists"
        
    else:
        message = "OSError: The download failed!"
        
    if display:
        text(message, INDEX, color="red", bold="A")
        line()
        
    else:
        termcolor.cprint(message, "red")
        
    exit()
    
#Deletes a file
def delete(path, target, display):
    global INDEX
    
    full_path = "%s/%s" %(path, target)
    
    if display:
        message = "Removing '%s'" %target
        text(message, INDEX)
    
    os.remove(full_path)
    
    return True
    
#Retuns video link and name by using clipboard
def by_clip(display):
    global INDEX
    
    link = subprocess.check_output(["xclip", "-o"])
    link = str(link).lstrip("b").strip("'")
    name = link_to_name(link)
    
    return (link, name)

#Returns video link and name by using provided name
def by_name(name, choice, display):
    global INDEX
    
    DOWNLOAD    = "https://www.youtube.com%s"
    song_index  = 0
    
    if display:
        message = "Finding matching video for '%s'" %name
        text(message, INDEX)
        
    names, links = name_to_link(name)
    names, links = filtering(names, links)
    
    if choice and display:
        message = "Multiple matching videos found:"
        text(message, INDEX)

        for index, sname in enumerate(names):
            song_index = "[%s] " %(" "*(index+1 < 10) + str(index+1))
            song_name  = html.unescape(sname)
            message = song_index + song_name

            text(message, None, bold=4)

        while True:
            message = "     Which song would you like to download"
            text(message, None, end = " ")
            song_index = input()

            try:
                song_index = int(song_index)
                assert (0 < song_index <= 20)
                break

            except AssertionError:
                text("That is not a valid number!", None)

            except ValueError:
                text("That is not a number!", None)

        song_index -= 1

        message = "Selected %s" %html.unescape(names[song_index])
        text(message, INDEX)
    
    elif display:
        message = "Matching video found: '%s'" %html.unescape(names[song_index])
        text(message, INDEX)
    
    return (DOWNLOAD %links[song_index], names[song_index])

###############################################################################
#Main
###############################################################################

#Main function
def main(options):
    global INDEX
    
    display = not options["--silent"]
    if display:
        line()
        
    name = options["<Name>"]
    clip = options["--clip"]
    
    if name:
        choice = options["--choice"]
        link, name = by_name(name, choice, display)
    
    elif clip:
        link, name = by_clip(display)
    
    if options["--name"]:
        name = options["<Name>"]
         
    video_format = options["--Vf"]
    audio_format = options["--Af"]
    file_path    = path(options, display)
    
    if display:
        message = "Downloading the video in .%s format" %video_format
        text(message, INDEX)
        
    download    = download_video(link, name, file_path, video_format)
    convert     = not options["--video"]
    target_file = "%s.%s" %(name, video_format)
    
    if download and convert:
        if display:
            message = "Converting the file to .%s format" %audio_format
            text(message, INDEX)
        
        video_to_mp3(file_path, target_file, audio_format)
        
        if not options["--both"]:
            delete(file_path, target_file, display)
            
    elif not download:
        failed_download(file_path, target_file, display)
    
    if display:
        text("Done!", INDEX, bold = "A")
        line()
        
if __name__ == "__main__":
    options = arguments()
    main(options)
    
    

"""
    
    display    = docopt_args["--silent" ]
    both_files = docopt_args["--both"   ]
    video_only = docopt_args["--video"  ]
    name_keep  = docopt_args["--name"   ]
    choosing   = docopt_args["--choice" ]
    autoplay   = docopt_args["--play"   ]
    
"""
    

