This is just a little project of mine to automaticly download multiple anime episodes from gogoanime (current domain https://anitaku.to).
Since the download servers have a download limit i added multithreading. One episode downloads at 3.3MBit/s, which means in order to get everything out of your own network you can use multiple threads for multiple episodes (note that the download time for single episodes is not affected by the number of threads). If you have a 50MBit Network (you can test this with almost every speedtest out there) you can calculate the number of threads: 50/3.3 ~ 15

1. Install the requirements: pip install -r requirements.txt
2. Specify the anime you want to search for
3. Select one of the found animes
4. Select which episodes you want to download (only from x to y currently)
5. Select a foldername that will either be created or used (if you want it somewhere else than the ./downloads you can specify the base path for all downloads in the setup.json file)
6. Wait 
It apparently can also happen, that an episode is not downloaded correctly, in that case just redownload it.

If the domain name has changed again, change the gogoanime_main in the setup.json file. In case a weird error apears the hardcoded captcha might be outdated, maybe this will get fixed.
To change the quality of the downloads you can change it in the setup (360, 480, 720 or 1080), if a download in the prefered quality is not available the highest quality will automaticly be chosen. If the quality is not 1080p the time estimates might be very inaccurate.