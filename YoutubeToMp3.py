from pytube import YouTube

import termcolor
import requests
import pydub
import html
import re

def download_video(link, name, path="/home/icebox", file_type="mp4"):
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

    video.download(path)

    if display:
        termcolor.cprint("4."         , "cyan" , attrs=["bold"] , end=""  )
        termcolor.cprint("|"          , "red"                   , end=""  )
        termcolor.cprint("Done!"      , "green", attrs=["bold"] , end="\n")
        termcolor.cprint("--+"+"-"*98 , "red"  , attrs=["bold"] , end="\n")

def find_video_link(name, choice = False, override = False):
    
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

def get(name, displayc = True, convert = True):
    global display
    display = displayc

    if display:
        termcolor.cprint("--+"+"-"*98 , "red" , attrs=["bold"], end="\n")
        termcolor.cprint("1."         , "cyan", attrs=["bold"], end=""  )
        termcolor.cprint("|"          , "red"                 , end=""  )
        termcolor.cprint("Finding matching video for '%s'" \
                                %name , "green"               , end="\n")

    values = find_video_link(name, choice = True)

    download_video(*values)

    if convert == True:
        pass
