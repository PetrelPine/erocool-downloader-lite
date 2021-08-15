# EroCool Downloader Lite

--- 

## How to Use

You can find the executable file in [releases](https://github.com/PetrelPine/EroCoolDownloaderLite/releases), or you can clone this repository and make your own changes.

##### Mode 1: Download from Links

You can enter links of detail page or list page.

+ If it's a detail page link, it will download target gallery **without any restrictions**. 

+ If it's a list page link, it will ask you to enter page number. '6-10' means download page 6-10, '6-' means download all pages from page 6 to last page, '-10' or '10' means download all pages from page 1 to page 10. **Restrictions will be enabled when download from list page**, galleries with excluded tags and galleries without chinese version will not be downloaded. 

##### Mode 2: Download Daily Ranked Galleries

It will download all galleries in daily-ranked gallery list page. ***(restrictions are enabled)***

##### Mode 3: Collect Covers

Collect all covers from existing galleries. *(white output means cover exists;  green output means cover is collected successfully; yellow output means cover is missing but gallery has excluded tags or gallery has no chinese version; red output means cover is missing.)*

##### Mode 4: Resume Incomplete Downloads

It will load all incomplete **detail** links from '_incomplete_links.json' file, and start to download these galleries using mode 1.

##### Mode 5: Open Gallery with Specific Name

It will open target gallery folder if you enter the correct name of the gallery, otherwise it will only open the 'Gallery' folder. 

##### Tips:

+ If you want to stop download, just close the program window, the progress is already saved. 

+ All galleries are stored under 'Gallery' folder and all covers are stored under 'Cover' folder. All incomplete links are stored in '_incomplete_links.json' file.

+ You can check incomplete list page links in '_incomplete_links.json' file. *(bug: incomplete list page link will not be removed even it is complete)*

--- 

## Enjoy!

I'm looking forward to your suggestions.

*If you like this repository, please give it a star for support :)*
