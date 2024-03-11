This is just a little project of mine to automaticly download multiple anime episodes from gogoanime (current domain https://anitaku.to).
I plan on implementing multithreading or something similar, because the server is capped at around 3.3Mbit/s, which is very slow (a 300MB episode takes around 13 Minutes or 2.6s for 1MB).

1. Install the requirements: pip install -r requirements.txt
2. Specify the anime you want to search for
3. Select one of the found animes
4. Select which episodes you want to download (only from x to y currently)
5. Select a foldername that will either be created or used (if you want it somewhere else than the ./downloads you can specify the base path for all downloads in the setup.json file)
6. Wait 
It apparently can also happen, that an episode is not downloaded correctly, in that case just redownload it.

If the domain name has changed again, change the gogoanime_main in the setup.json file. In case a weird error apears the hardcoded captcha might be outdated, maybe this will get fixed.
To change the quality of the downloads you can change it in the setup (360, 480, 720 or 1080), if a download in the prefered quality is not available the highest quality will automaticly be chosen. If the quality is not 1080p the time estimates might be very inaccurate.