#!/usr/bin/python

import subprocess
import os
import re
import sys

twitchdl_bin="twitch-dl" # change this to /usr/bin/twitch-dl or wherever your main script file is.

# prints a line if debug is true
def dprint(text):
    if debug:
        print("Debug: " + text)


# the command function
def tdl(func, param, work_dir, output_to_console): # output_to_console is a debug command; if it's true, we get a lot more feedback.
    dprint(f"func = {func}")
    dprint(f"param = {param}")
    command = f"{twitchdl_bin} {func} {param}" # prefix the command. this is always the same
    if(func == "download"):
        command = f"{command} -q source --skipall" # if we're downloading, do it at max quality
    else:
        command = f"{command} -a" # the only other functions that could be called are "clips" and "videos" and those just need -a. remove -a for faster testing
    dprint(f"command = {command}")

    # make sure the directories are there
    os.makedirs(work_dir, exist_ok=True)
    original_dir = os.getcwd()
    os.chdir(work_dir)

    #logic to find out if exists / todo: reduce nesting
    if (func == "download"):
        is_clip = True
        dprint (f"trying to open .library in {work_dir}")
        dprint (f"we are in {os.getcwd()}")
        with open('.library', 'r') as library_file:
            for line in library_file:
                dprint(f"line   = {line.split(' ')[0]}")
                dprint(f"target = {param}")
                if (param == line.split(' ')[0]):
                    #dprint("match")
                    dprint(f"{param}")
                    dprint("  exists as:")
                    dprint(f"{line.split(' ')[1]}")
                    os.chdir(original_dir) # change back to the original directory
                    return (f"{param} {line.split(' ')[1]}")
    else:
        is_clip = False

    dprint (f"is_clip = {is_clip}")

    dprint (f"running command: {command}")
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) # make it do the thing

    output_lines = []

    # process and log output in real-time
    while True:
        output = process.stdout.readline()
        if process.poll() is not None and output == b'':
            break
        if output:
            line = output.decode().strip() # i actually forgot what this does already
            if line.startswith("Downloaded "):  # disregard download progress when logging because holy shit
                continue
            if (func == "download"):
                if (line.startswith("Target: ")): # todo: reduce nesting
                        targetfile = line.replace('Target: \x1b[94m', '').replace('\x1b[0m', '')
                elif (line.startswith("Output: ")):
                        targetfile = line.replace('Output: \x1b[94m', '').replace('\x1b[0m', '')
                        dprint (f"looking for file {targetfile}")
                if (line.startswith("Downloaded: ")) or (line.startswith("Target file exists")):  # Check for successful download
                    dprint("SUCCESS")
                    os.chdir(original_dir) # change back to the original directory
                    return (f"{param} {targetfile.strip()}")

            if output_to_console:
                print(line)
            output_lines.append(line)

    stderr = process.stderr.read().decode()
    if stderr:
        if output_to_console:
            print(f"Error: {stderr}")
        output_lines.append(f"Error: {stderr}")

    os.chdir(original_dir) # change back to the original directory

    # write output to log file and return it unless we're downloading a clip'
    if output_to_console:
        with open('log.txt', 'w') as log_file:
            log_file.write('\n'.join(output_lines) + '\n')

    return '\n'.join(output_lines)


# find and extract video ids
def extract_video_ids(text):
    video_lines = re.findall(r'^\x1b\[1mVideo \d+', text, re.MULTILINE)
    cleaned_ids = [re.sub(r'^\x1b\[1mVideo (\d+).*', r'\1', line) for line in video_lines]
    return ' '.join(cleaned_ids)


# find and extract clip urls
def extract_clip_urls(text):
    urls = re.findall(r'^\x1b\[3mhttps://clips.twitch.tv/\S+', text, re.MULTILINE)
    cleaned_urls = [url.replace('\x1b[3m', '').replace('\x1b[0m', '') for url in urls]
    return ' '.join(cleaned_urls)


# we need to make sure the .library files exist and do a sanity check to make sure it's not corrupted. / todo: the sanity check i made fucking sucks
def check_library(path):
    liberror = False
    libcheck = []

    if not (os.path.isfile(f'{path}/.library')):
        libmake = open(f"{path}/.library", "x")
        libmake.close()
    with open(f'{path}/.library', 'r') as library_file:
        dprint(".library file opened")
        for librline in library_file:
            libline = librline.strip()
            if (libline != ""):
                dprint(f".library sanity check line = {libline}")
                dprint(f"{len(libline.split(' '))}")
                if (len(libline.split(' ')) != 2):
                    dprint("spaces error in .library")
                    liberror = True
                elif not (os.path.isfile(f"{path}/{libline.split(' ')[1].strip()}")):
                    dprint(f"{path}/{libline.split(' ')[1].strip()} doesnt exist")
                else:
                    libcheck.append(libline)
    with open(f'{path}/.library', 'w') as library_file:
        library_file.write('\n'.join(libcheck) + '\n')


def crosscheck(downloads, folder):
    #logic to find out if exists / todo: reduce nesting
    library_list = []
    return_list = []
    with open(f'{folder}/.library', 'r') as library_file: # we combine each word in the library file into a single dimension array
        for line in library_file:
            line = line.strip()
            if (line != ""):
                library_list.append(line.split(' ')[0])
                library_list.append(line.split(' ')[1])

    for twitchid in downloads:
        try:
            index = library_list.index(twitchid) # if twitchid in library_list else -1
            if index < len(library_list) - 1 :
                print(f"Skipping {twitchid}...")
        except ValueError:
            return_list.append(twitchid)
            print(f"Grabbing {twitchid}...")
    dprint(f"{folder}")
    dprint(f"{return_list}")
    return return_list


def main():
    global debug
    debug = False
    if len(sys.argv) > 1:
        if sys.argv[1] == f"-d": # why doesn't this work without the f it should work without the f shouldnt it am i crazy
            debug = True

    with open('subscriptions.txt', 'r') as subs:
        for line in subs:
            channel = line.strip()

            # directory creation
            os.makedirs(f"./twitch-dl/{channel}/videos", exist_ok=True)
            os.makedirs(f"./twitch-dl/{channel}/clips", exist_ok=True)
            os.makedirs("/tmp/tdl-all/", exist_ok=True)

            videos_path = f"./twitch-dl/{channel}/videos"
            clips_path = f"./twitch-dl/{channel}/clips"

            # search .library for missing files and remove those lines here
            check_library(videos_path)
            check_library(clips_path)

            # get videos
            print(f"Checking {channel}'s videos...")
            videos_output = extract_video_ids(tdl("videos", channel, videos_path, False))
            videos_list = videos_output.split(' ') # need to join space separated result into array
            missingfiles = crosscheck(videos_list, videos_path) # MIGHT BE EMPTY!
            dprint(f"{missingfiles}")
            if len(missingfiles) > 0:
                newlib = [] # we build a new library each time
                for video_id in missingfiles: # todo: iterate through videos_output instead. do the same for clips
                    dprint(f"{video_id}")
                    newlibline = tdl("download", video_id, videos_path, True)
                    dprint(f"\n\nsuccess! appending {newlibline} to new .library file\n")
                    dprint(f"{newlibline}")
                    newlib.append(newlibline)
                with open(f'{videos_path}/.library', 'a') as library_file: # we append the old library with the new one
                    library_file.write('\n'.join(newlib).strip().replace('\n\n', '\n')) # i don't know why python loves to add so many carriage returns

            # get clips
            print(f"Checking {channel}'s clips...")
            clips_output = extract_clip_urls(tdl("clips", channel, clips_path, False))
            clips_list = clips_output.split(' ') # need to join space separated result into array
            missingfiles = crosscheck(clips_list, clips_path) # MIGHT BE EMPTY!
            if len(missingfiles) > 0:
                newlib = [] # we build a new library each time
                for clip_url in missingfiles:
                    newlibline = tdl("download", clip_url.strip(), clips_path, True)
                    dprint(f"\n\nsuccess! appending {newlibline} to new .library file\n")
                    dprint(f"{newlibline}")
                    newlib.append(newlibline)
                with open(f'{clips_path}/.library', 'a') as library_file: # we append the old library with the new one
                    library_file.write('\n'.join(newlib).strip().replace('\n\n', '\n'))

if __name__ == "__main__":
    main()
