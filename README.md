# EroCool Downloader Lite

## How to Use

+ **You can find the executable file in [releases](https://github.com/PetrelPine/EroCoolDownloaderLite/releases), or you can clone this repository and make your own changes.**

+ The executable file was packed on Windows 10, and I can run it smoothly. I am not sure if it still works on other versions of Windows. In other platforms apart from Windows, you need to use pyinstaller to pack the executable file again.

## Four Modes

### 1 - Download from Links

+ In mode 1, you can enter multiple links of detail page or list page.

  + If it's a detail page link, it will download target gallery **without any restrictions**.

  + If it's a list page link, it will ask you to enter page range. '6-10' means download from page 6 to page 10, '6-' means download all pages from page 6 to last page, '-10' or '10' means download all pages from the first page to page 10. **Restrictions will be enabled when download from list page**, galleries with excluded tags and galleries without chinese version will not be downloaded.

  + If you entered both detail page links and list page links, detail page links will be downloaded first. When it comes to list page links, it will ask you to enter the page range.

### 2 - Collect Covers

+ It will collect all covers from existing galleries. The collection log will be shown in the console.

### 3 - Resume Incomplete Downloads

+ It will load all incomplete **detail** links from '_incomplete_links.json' file, and start to download these galleries using mode 1.

### 4 - Open Gallery by Name

+ It will open target gallery folder if you enter the correct name of the gallery, otherwise it will only open the 'Gallery' folder.

## Tips

+ If you want to stop download process, just close the program window, the progress is already saved as the download goes.

+ All galleries are stored under 'Gallery' folder and all covers are stored under 'Cover' folder.

+ You can check incomplete links in '_incomplete_links.json' file. You can also add links to '_incomplete_links.json' file if you follow the pattern.

## Enjoy!

I'm looking forward to your suggestions.

*If you like this repository, please give it a star for support :)*
