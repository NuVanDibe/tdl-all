the tl;dr is that you can use this to download entire channels' clips and vods.

instructions:
download twitch-dl.pyz: https://github.com/ihabunek/twitch-dl/releases
if my commit hasn't been merged, you'll want to clone my repo for twitch-dl and merge/overwrite the contents of twitch-dl.pyz with mine: https://github.com/NuVanDibe/twitch-dl
download the tdl-all.py file
edit the twitchdl_bin="twitch-dl" line to point to wherever you're keeping twitch-dl.pyz. i like to softlink it to /usr/bin/twitch-dl
optional: add tdl-all.py to path
navigate to the folder into which you want to download your channels
create a text document called subscriptions.txt which contains a list of channels you want to download, one on each line
run [path-to]/tdl-all.py

it will create folder tree like this: twitch-dl/channelname/clips

It will also create a .library file in each channel's clips & videos folder which it uses to index what it's already downloaded.

todo: add option to incorporate auth tokens into the subscriptions.txt file to allow for downloading of subscriber-only vods
