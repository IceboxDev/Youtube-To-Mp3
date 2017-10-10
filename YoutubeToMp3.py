#!/usr/bin/env python3

"""Youtube To MP3 Converter

Usage:
    Youtube vid   <Name> [-c][-s][-v][-b][-n][-p] [--sub=<s>] [--path=<p>] [--Vf=<vf>] [--Af=<af>]
    Youtube clip         [-s][-v][-b][-p][-t]     [--sub=<s>] [--path=<p>] [--Vf=<vf>] [--Af=<af>]

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
    -t, --text          : Use clipboard contents as video name
    -h, --help          : Show this screen.
    --version           : Show version.

"""

#Imports
from pydub  import AudioSegment
from pytube import YouTube
from docopt import docopt

import subprocess
import pyperclip
import termcolor
import requests
import getpass
import errno
import html
import re
import os

#Constants
VERSION = 3.1
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
    
    if index:
        INDEX += 1
    
###############################################################################
#Scraping and link functions
###############################################################################

#Youtube video link to it's name
def link_to_name(link):
    r        = requests.get(link)
    source   = r.text

    regex    = r'(?<=<meta itemprop="name" content=")(.*?)(?=">)'
    match    = re.search(regex, source)
    name     = match.group(0)

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

#Converts a playlist link to a list of video links
def playlist_to_links(link):
    dllink  = "https://www.youtube.com%s"
    r       = requests.get(link)
    source  = r.text

    names_regex = r'(?<=data-title=")(.*?)(?=")'
    links_regex = r'(?<=dir="ltr" href=")(.*?)(?=">)'

    names       = re.findall(names_regex, source)
    links       = re.findall(links_regex, source)
    
    links       = links[(len(links) == 101):]
    links       = [dllink %html.unescape(links[i]).split("&")[0] \
                   for i in range(len(links)) if names[i] != "[Privates Video]"]

    return links

#Converts a user/channel link to a list of video links
def user_to_links(link, best=True):
    dllink = "https://www.youtube.com%s"
    kbest  = "?view=0&flow=grid&sort=p"

    link   = link.split("/")
    key    = link.index("www.youtube.com")
    ktype  = link[key+1]
    kname  = link[key+2]

    build  = "https://www.youtube.com/%s/%s/videos%s" \
             %(ktype, kname, kbest*best)

    r      = requests.get(build)
    source = r.text

    names_regex = r'(?<=dir="ltr" title=")(.*?)(?="  aria-describedby)'
    links_regex = r'(?<=<a href=")(.*?)(?=" class="yt-uix-sessionlink")'

    names  = re.findall(names_regex, source)
    links  = re.findall(links_regex, source)

    links  = links[len(links) == 31:]
    links  = [dllink% i for i in links]
    
    return links

#Filters out unwanted links
def filtering(names, links, filt="watch", nfilt="list="):
    #Filters: channel/user/watch/playlist
    
    names = names[len(names) == 21:]
    links = links[len(links) == 21:]
   
    invalid_links = []
    for index in range(len(links)):
        if filt not in links[index] or nfilt in links[index]:
            invalid_links.append(index)

    for index in invalid_links[::-1]:
        del names[index]
        del links[index]
    
    return (names, links)

#Validates link
def validate(link):
    regex = re.compile(
    r'^(?:http|ftp)s?://'
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
    r'localhost|'
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    r'(?::\d+)?'
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if regex.match(link) == None:
        link = "http://" + link

        if regex.match(link) == None:
            return (False, None, link)

    session  = requests.Session()
    response = session.head(link, allow_redirects = True).url

    A = regex.match(response) != None
    B = "youtube" in response
    U = unavailable(response)

    if A and B:
        if   "watch"    in response:
            if U:
                return (True, "U", U       ) #U for unavailabe
            
            else:
                return (True, "V", response) #V for video

        elif "user"     in response or "channel" in response:
            return (True, "C", response) #C for channel

        elif "playlist" in response:
            return (True, "P", response) #P for playlist

        else:
            return (True, "E", response) #E for error

    else:
        return (True, False, response)

#Checks if the video is available
def unavailable(link):
    r       = requests.get(link)
    source  = r.text

    regex1  = r'(?<=<h1 id="unavailable-message" class="message">)(.*?)(?=</h1>)'
    regex2  = r'(?<=<div id="player-unavailable" class=")(.*?)(?=player-width)'

    match1  = re.search(regex1, source, re.DOTALL)
    match2  = re.search(regex2, source, re.DOTALL)

    try:
        hidden = match2.group(0).strip()
        assert hidden == "hid"
        return False

    except AttributeError:
        error = match1.group(0).strip()
        return error

###############################################################################
#Download and conversion functions
###############################################################################

#Given link, downloads youtube video
def download_video(link, name, path, video_format):
    yt = YouTube(link)
    yt.set_filename(name)
    
    regex   = r"\d{3,4}p"

    try:
        quality = str(yt.filter(video_format)[-1])
        match   = re.search(regex, quality)
        res     = match.group(0)
        video   = yt.get(video_format, res)

        video.download(path)
        return True
        
    except OSError as error:
        if error.errno == 13:
            return 4

        else:
            return 2
    
    except IndexError:
        return 3

#Converts the video file to mp3
def video_to_mp3(path, target, audio_format):
    input_file  = "%s/%s"    %(path, target)
    output_file = "%s/%s.%s" %(path, target.split(".")[0], audio_format)
    
    AudioSegment.from_file(input_file).export(output_file, format=audio_format)
    
    return output_file

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

        args["--video"] = not args["--video"]

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
                text(message, INDEX)
                
            os.makedirs(full_path)
        
        return full_path
    
    else:
        return path

#Handles failed downloads
def failed_download(file_path, target, error, display):
    global INDEX
    
    full_path = "%s/%s" %(file_path, target)
    
    if os.path.isfile(full_path) and error == 2:
        message = "Error: A file with this name already exists"
    
    elif error == 3:
        message = "Error: Unable to download the video with specified format"

    elif error == 4:
        message = "Permission denied"

    else:
        message = "Error: The download failed!"
        
    if display:
        text(message, INDEX, color="red", bold="A")
        line()
        
    else:
        termcolor.cprint(message, "red")
        
    exit()

#Handles invalid clipboard
def failed_link(clipboard, display):
    message1 = "Error: Clipboard contains - '%s'" %clipboard
    message2 = "That is not a valid youtube video link!"
    message3 = "Would you like to use clipboard content as video name? [y/n] "
    message4 = "Invalid input. Input should be either 'y' or 'n'"

    if display:
        text(message1, INDEX, color="red", bold="A")
        text(message2, None , color="red", bold="A")

    else:
        termcolor.cprint(message1, "red")
        termcolor.cprint(message2, "red")

    while True:
        if display:
            text(message3, None , color="red", bold="A", end="")
        
        else:    
            termcolor.cprint(message3, "red", end="")
        
        inp = input().lower()
            
        if inp == "y" or inp == "n":
            break
        
        else:
            if display:
                text(message4, None , color="red", bold="A")

            else:
                termcolor.cprint(message4, "red")

    if inp == "y":
        return True 

    if display:
        line()
    
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

    if len(links) == 0:
        message = "No videos with that name were found!"
        
        if display:
            text(message, INDEX, color="red", bold="A")
            line()

        else:
            termcolor.cprint(message)

        exit()

    if choice and display:
        message = "Matching video%s found:" %("s" * (len(links) > 1))
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
                assert (0 < song_index <= len(names))
                break

            except AssertionError:
                text("     That is not a valid number!", None)

            except ValueError:
                text("     That is not a number!", None)

        song_index -= 1

        message = "Selected video: '%s'" %html.unescape(names[song_index])
        text(message, INDEX)
    
    elif display:
        message = "Matching video found: \'%s\'" %html.unescape(names[song_index])
        text(message, INDEX)
    
    return (DOWNLOAD %links[song_index], names[song_index])

###############################################################################
#Main
###############################################################################

#Function that handles the input
def main(options):
    global INDEX
    global PLAYLIST_LEN

    display = not options["--silent"]

    if display and not options["--text"]:
        line()
        
    name = options["<Name>"]

    if   options["vid" ]:
        choice = options["--choice"]
        link, name = by_name(name, choice, display)

        return (name, [link])

    elif options["clip"]:
        clipboard = pyperclip.paste()
        link, opt, content = validate(clipboard)
        
        if  options["--text"]:
            options["<Name>"] = clipboard
            options["--text"] = False
            options["clip"  ] = False
            options["vid"   ] = True

            return None
        
        elif not link:
            failed_link(clipboard, display)

            options["<Name>"] = clipboard
            options["clip"  ] = False
            options["vid"   ] = True

            return None

        else:
            if   opt == "V":
                if display:
                    message = "Converting the video link"
                    text(message, INDEX)

                name = link_to_name(content)

                if display:
                    message = "Video name - '%s'" %html.unescape(name)
                    text(message, INDEX)

                return (name, [content])
            
            elif opt == "C":
                links = user_to_links(content)
                PLAYLIST_LEN = len(links)

                return (None, links) 

            elif opt == "P":
                links = playlist_to_links(content)
                PLAYLIST_LEN = len(links)

                return (None, links)
            
            elif opt == "U":
                message = content

                if display:
                    text(message, INDEX, color="red", bold="A")
                    line()

                else:
                    termcolor(message, "red")

                exit()

            else:
                message = "'%s' is an invalid %slink!" %(content, "YouTube "*(opt=="E")) 

                if display:
                    text(message, INDEX, color="red", bold="A")
                    line()

                else:
                    termcolor.cprint(message, "red")

                exit()

#Function that handles the rest
def get(name, link, options):
    global INDEX
    global song_id

    display = not options["--silent"]

    if options["--name"]:
        name = options["<Name>"]

    elif not name:
        name = link_to_name(link)

        if display:
            message = "Video [%s/%s] - '%s'" %(song_id, PLAYLIST_LEN, html.unescape(name))
            text(message, INDEX)

    name = html.unescape(name)
    name = name.replace("/", "\\")

    autoplay     = options["--play"]
    video_format = options["--Vf"  ]
    audio_format = options["--Af"  ]
    file_path    = path(options, display)
    
    if display:
        message = "Downloading the video in .%s format" %video_format
        text(message, INDEX)
        
    download    = download_video(link, name, file_path, video_format)
    convert     = not options["--video"]
    target_file = "%s.%s" %(name, video_format)

    if convert and download == True:
        if display:
            message = "Converting the file to .%s format" %audio_format
            text(message, INDEX)
        
        song = video_to_mp3(file_path, target_file, audio_format)
        
        if not options["--both"]:
            delete(file_path, target_file, display)
            
    elif download == 2 or download == 3 or download == 4:
        failed_download(file_path, target_file, download, display)
    
    if display:
        
        if autoplay and convert:
            message = "Now playing: '%s'" %song.split("/")[-1]
            text(message, INDEX)
            play_target = song.split("/")[-1]
            
        elif autoplay:
            message = "Now playing: '%s'" %target_file
            text(message, INDEX)
            play_target = target_file
            
    else:
        if autoplay and convert:
            play_target = song.split("/")[-1]
        
        elif autoplay:
            play_target = target_file

    if autoplay:
        song_path = "%s/%s" %(file_path, play_target)
        os.system("xdg-open '%s'" %song_path)
        options["--play"] = False

if __name__ == "__main__":
    options = arguments()
    line_dr = False
    song_id = 1

    while True:
        output = main(options)

        if output:
            name, links = output
            break

    for link in links:
        if not options["--silent"] and line_dr:
            INDEX   = 1
            line()

        get(name, link, options)

        line_dr = True
        song_id += 1

    if not options["--silent"]:
        text("Done!", INDEX, bold = "A")
        line()
