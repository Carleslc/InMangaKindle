# Spanish Manga for Kindle / Ebook
## Manga en Español para Kindle / Ebook

### Dependencies

- [Python 3.6](https://www.python.org/downloads/)
- (EPUB/MOBI format) [Kindle Comic Converter](https://github.com/ciromattia/kcc)
- (MOBI format) [KindleGen](https://www.amazon.com/gp/feature.html?ie=UTF8&docId=1000765211)
- (Optional) [SendToKindle](https://www.amazon.com/gp/sendtokindle)

### Usage

`python3.6 manga.py -h`

```
usage: manga.py [-h] [--chapters CHAPTERS] [--directory DIRECTORY] [--single]
                [--rotate] [--profile PROFILE] [--format FORMAT] [--fullsize]
                manga

positional arguments:
  manga                 manga to download

optional arguments:
  -h, --help            show this help message and exit
  --chapters CHAPTERS, --chapter CHAPTERS
                        chapters to download. Format: start..end or chapters
                        with commas. Example: --chapters "3..last" will
                        download chapters from 3 to the last chapter,
                        --chapter 3 will download only chapter 3, --chapters
                        "3, 12" will download chapters 3 and 12, --chapters
                        "3..12, 15" will download chapters from 3 to 12 and
                        also chapter 15. If this argument is not provided all
                        chapters will be downloaded.
  --directory DIRECTORY
                        directory to save downloads. Default: ./manga
  --single              pack all chapters in only one e-reader file. If this
                        argument is not provided every chapter will be in a
                        separated file
  --rotate              rotate double pages. If this argument is not provided
                        double pages will be splitted in 2 different pages
  --profile PROFILE     Device profile (Available options: K1, K2, K34, K578,
                        KDX, KPW, KV, KO, KoMT, KoG, KoGHD, KoA, KoAHD,
                        KoAH2O, KoAO) [Default = KPW (Kindle Paperwhite)]
  --format FORMAT       Output format (Available options: PNG, PDF, MOBI, EPUB,
                        CBZ) [Default = MOBI]. If PNG is selected then no
                        conversion to e-reader file will be done
  --fullsize            Do not stretch images to the profile's device
                        resolution
```

### Examples

Default screen resolution is for Kindle Paperwhite device profile.

- `python manga.py "one piece" --chapters 880..last --single` will download _One Piece_ chapters from 880 to the last chapter available and pack them into one single MOBI file

- `python manga.py "one piece" --chapters 880..last --format PDF --single` will result in the same as above but in PDF instead MOBI

- `python manga.py "shingeki no kyojin" --chapter last --format EPUB` will download the last chapter of _Shingeki no Kyojin_ as EPUB

- `python manga.py "dragon ball" --chapters "1, 2, 8..11"` will download chapters 1, 2, 8, 9, 10, 11 of _Dragon Ball_ as different MOBI files

### TO DO
- Explain with images how this works (scraping)
- Additional chapter placeholder "lastDownloaded..last"
