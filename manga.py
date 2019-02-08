#!/usr/bin/python3.6
# -*- coding: utf-8 -*-

import os
import json
import argparse
from requests import get, post
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from colorama import Fore, Style, init
from multiprocessing import freeze_support

WEBSITE = "https://inmanga.com"
IMAGE_WEBSITE = f"{WEBSITE}/page/getPageImage/?identification="
CHAPTERS_WEBSITE = f"{WEBSITE}/chapter/getall?mangaIdentification="
CHAPTER_PAGES_WEBSITE = f"{WEBSITE}/chapter/chapterIndexControls?identification="
MANGA_WEBSITE = f"{WEBSITE}/ver/manga"

SEARCH_URL = "https://inmanga.com/manga/getMangasConsultResult"
SEARCH_QUERY = "filter%5Bgeneres%5D%5B%5D=-1&filter%5BqueryString%5D=MANGA&filter%5Bskip%5D=0&filter%5Btake%5D=10&filter%5Bsortby%5D=5"

MANGA_DIR = './manga'

FILENAME_KEEP = set(['_', '-', ' ', '.'])
DIRECTORY_KEEP = FILENAME_KEEP | set(['/'])
EXTENSION_KEEP = set('.')

def set_args():
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument("manga", help="manga to download")
    parser.add_argument("--chapters", "--chapter", help='chapters to download. Format: start..end or chapters with commas. Example: --chapters "3..last" will download chapters from 3 to the last chapter, --chapter 3 will download only chapter 3, --chapters "3, 12" will download chapters 3 and 12, --chapters "3..12, 15" will download chapters from 3 to 12 and also chapter 15. If this argument is not provided all chapters will be downloaded.')
    parser.add_argument("--directory", help=f"directory to save downloads. Default: {MANGA_DIR}", default=MANGA_DIR)
    parser.add_argument("--single", action='store_true', help="pack all chapters in only one e-reader file. If this argument is not provided every chapter will be in a separated file")
    parser.add_argument("--rotate", action='store_true', help="rotate double pages. If this argument is not provided double pages will be splitted in 2 different pages")
    parser.add_argument("--profile", help='Device profile (Available options: K1, K2, K34, K578, KDX, KPW, KV, KO, KoMT, KoG, KoGHD, KoA, KoAHD, KoAH2O, KoAO) [Default = KPW (Kindle Paperwhite)]', default='KPW')
    parser.add_argument("--format", help='Output format (Available options: PNG, PDF, MOBI, EPUB, CBZ) [Default = MOBI]. If PNG is selected then no conversion to e-reader file will be done', default='MOBI')
    parser.add_argument("--fullsize", action='store_true', help="Do not stretch images to the profile's device resolution")
    parser.add_argument("--cache", action='store_true', help="Do not download episode but get from local directory")
    args = parser.parse_args()

def print_colored(message, *colors):
    def printnoln(s):
        print(s, end='', flush=True)
    for color in colors:
        printnoln(color)
    print(message)
    printnoln(Style.RESET_ALL)

def error(message):
    print_colored(message, Fore.RED, Style.BRIGHT)
    exit()

def print_dim(s, *colors):
    print_colored(s, Style.DIM, *colors)

def print_source(html_soup):
    print_dim(html_soup.prettify())

def success(request, text='', ok=200, print_ok=True):
    if request.status_code == ok:
        if print_ok:
            print_colored(text if text else request.url, Fore.GREEN)
        return True
    else:
        text = f'{text}\n' if text else ''
        print_colored(f'{text}[{request.status_code}] {request.url}', Fore.RED)
        return False

def exit_if_fails(request):
    if not success(request, print_ok=False):
        exit(1)

def write_file(path, data):
    dirname = os.path.dirname(path)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    with open(path, 'wb') as handler:
        handler.write(data)

def strip_path(path, keep):
    return ''.join(c for c in path if c.isalnum() or c in keep).strip()

def encode_path(filename, extension, directory='.'):
    return strip_path(f'{directory}/{filename}', DIRECTORY_KEEP) + '.' + strip_path(extension, EXTENSION_KEEP)

def download(filename, url, directory='.', extension='png', text='', ok=200):
    path = encode_path(filename, extension, directory)
    if os.path.isfile(path):
        text = text if text else path
        separation = ' ' * (20 - len(text))
        print_colored(f'{text}{separation}- Already exists', Fore.YELLOW)
        return False
    req = get(url)
    if success(req, text, ok, print_ok=bool(text)):
        data = req.content
        write_file(path, data)
        return True
    return False

def manga_directory(manga):
    return f'{MANGA_DIR}/{manga}'

def chapter_directory(manga, chapter):
    return f'{manga_directory(manga)}/{chapter}'

def check_exists_file(path):
    if os.path.isfile(path):
        print_colored(f'{path} - Already exists', Fore.YELLOW)
        return True
    return False

def files(dir, extension=''):
    def filename(file):
        return file.split('.')[-2]
    for file in os.listdir(dir):
        path = os.path.abspath(f'{dir}/{file}')
        if os.path.isfile(path) and file.endswith(extension):
            yield filename(file), path

def load_json(data, *keys):
    data = json.loads(data)
    for key in keys[:-1]:
        data = json.loads(data.get(key))
    return data.get(keys[-1])

def parse_chapters_range(chapters, last):
    global CHAPTERS

    def get_number(number):
        return last if number == 'last' else int(number)

    ranges = chapters.replace(' ', '').split(',')
    try:
        for r in ranges:
            split = r.split('..')
            if len(split) == 1:
                CHAPTERS.add(get_number(split[0]))
            else:
                CHAPTERS.update(range(get_number(split[0]), get_number(split[1]) + 1))
    except ValueError:
        error(f'Invalid chapters format')

def filename_chapter_range():
    min_chapter = min(CHAPTERS)
    max_chapter = max(CHAPTERS)
    return str(min_chapter) if min_chapter == max_chapter else f'{min_chapter}-{max_chapter}'

def split_rotate_2_pages(rotate):
    return str(1 if rotate else 0)

def single(single):
    return str(0 if single else 2)

def cache_convert(args):
    try:
        manga2ebook(args)
    except Exception as e:
        print(e)
        exit()

if __name__ == "__main__":

    # initialize console colors for windows.
    init()
    
    # PARSE ARGS

    set_args()

    MANGA_DIR = strip_path(args.directory, DIRECTORY_KEEP)

    CHAPTERS = set()

    download_all = not args.chapters

    if not args.profile:
        args.profile = 'KPW'

    MANGA = args.manga

    # SEARCH ANIME

    print_colored(f'Searching {MANGA}...', Style.BRIGHT)

    # Alternative Search: https://inmanga.com/OnMangaQuickSearch/Source/QSMangaList.json
    search = post(SEARCH_URL, data=SEARCH_QUERY.replace('MANGA', quote_plus(MANGA)), headers={'Content-Type': 'application/x-www-form-urlencoded'})
    exit_if_fails(search)

    search_href = BeautifulSoup(search.content, 'html.parser').find_all(True, recursive=False)

    results = []
    match = False
    for result in search_href:
        manga_href = result.get('href')
        if manga_href is None:
            error(f"Manga '{MANGA}' not found")
        manga = manga_href.split('/')[-2] # encoded title
        uuid = manga_href.split('/')[-1]
        manga_title = result.find('h4').get_text().strip() # may contain special characters
        if manga_title.upper() == MANGA.upper():
            match = True
            break
        results.append(manga_title)

    if not match and len(search_href) > 1:
        upper_titles = [title.upper() for title in results]
        error('There are several results, please select one of these:\n' + '\n'.join(upper_titles))

    # RETRIEVE CHAPTERS

    chapters_json = get(CHAPTERS_WEBSITE + uuid)
    exit_if_fails(chapters_json)

    chapters_full = load_json(chapters_json.content, 'data', 'result')
    chapters = {}

    if args.chapters:
        last = max([int(chapter['Number']) for chapter in chapters_full])
        parse_chapters_range(args.chapters, last)

    for chapter in chapters_full:
        number = chapter['Number']
        if download_all or number in CHAPTERS:
            chapters[number] = chapter['Identification']

    # DOWNLOAD CHAPTERS
    CHAPTERS = sorted(CHAPTERS)
    if not args.cache:
        downloaded = False

        for chapter in CHAPTERS:
            uuid = chapters.get(chapter)
            if uuid is None:
                print_colored(f'{manga_title} {chapter} not found', Fore.RED)
            else:
                print_colored(f'Downloading {manga_title} {chapter}', Fore.YELLOW, Style.BRIGHT)

                #url = f"{MANGA_WEBSITE}/{manga}/{chapter}/{uuid}"
                url = CHAPTER_PAGES_WEBSITE + uuid

                chapter_dir = chapter_directory(manga, chapter)
                page = get(url)
                if success(page, print_ok=False):
                    html = BeautifulSoup(page.content, 'html.parser')
                    pages = html.find(id='PageList').find_all(True, recursive=False)
                    for page in pages:
                        page_id = page.get('value')
                        page_number = int(page.get_text())
                        url = IMAGE_WEBSITE + page_id
                        download(page_number, url, chapter_dir, text=f'Page {page_number}/{len(pages)} ({100*page_number//len(pages)}%)')
                    downloaded = True

        if not downloaded:
            error("No chapters found")

    extension = f'.{args.format.lower()}'
    directory = manga_directory(manga)

    args.format = args.format.upper()

    if args.format != 'PNG':
        print_colored(f'Converting to {args.format}...', Fore.BLUE, Style.BRIGHT)

        if args.format == 'PDF':
            import img2pdf
            chapters_paths = []
            for chapter in CHAPTERS:
                chapter_dir = chapter_directory(manga, chapter)
                chapter_number_paths = sorted(list(files(chapter_dir, 'png')), key=lambda name_path: int(name_path[0]))
                chapter_paths = list(map(lambda name_path: name_path[1], chapter_number_paths))
                if args.single:
                    chapters_paths.extend(chapter_paths)
                else:
                    path = f'{MANGA_DIR}/{manga} {chapter}{extension}'
                    if not check_exists_file(path):
                        with open(path, "wb") as f:
                            f.write(img2pdf.convert(chapter_paths))
                        print_colored(f'DONE: {os.path.abspath(path)}', Fore.GREEN, Style.BRIGHT)
            if args.single:
                chapter_range = filename_chapter_range()
                title = f'{manga_title} {chapter_range}'
                path = f'{MANGA_DIR}/{manga} {chapter_range}{extension}'
                if not check_exists_file(path):
                    with open(path, "wb") as f:
                        f.write(img2pdf.convert(chapters_paths))
                    print_colored(f'DONE: {os.path.abspath(path)}', Fore.GREEN, Style.BRIGHT)
        else:
            # CONVERT TO E-READER FORMAT
            from kindlecomicconverter.comic2ebook import main as manga2ebook

            freeze_support()

            argv = ['--output', MANGA_DIR, '-p', args.profile, '--manga-style', '--hq', '-f', args.format, '--batchsplit', single(args.single), '-u', '-r', split_rotate_2_pages(args.rotate)]
            
            if not args.fullsize:
                argv.append('-s')

            if args.single:
                chapter_range = filename_chapter_range()
                title = f'{manga_title} {chapter_range}'
                print_colored(title, Fore.BLUE)
                argv = argv + ['--title', title, directory] # all chapters in manga directory are packed
                cache_convert(argv)
                path = f'{MANGA_DIR}/{manga} {chapter_range}{extension}'
                os.rename(f'{MANGA_DIR}/{manga}{extension}', path)
                print_colored(f'DONE: {os.path.abspath(path)}', Fore.GREEN, Style.BRIGHT)
            else:
                for chapter in CHAPTERS:
                    title = f'{manga_title} {chapter}'
                    print_colored(title, Fore.BLUE)
                    argv_chapter = argv + ['--title', title, chapter_directory(manga, chapter)]
                    cache_convert(argv_chapter)
                    path = f'{MANGA_DIR}/{manga} {chapter}{extension}'
                    os.rename(f'{MANGA_DIR}/{chapter}{extension}', path)
                    print_colored(f'DONE: {os.path.abspath(path)}', Fore.GREEN, Style.BRIGHT)
    else:
        print_colored(f'DONE: {os.path.abspath(directory)}', Fore.GREEN, Style.BRIGHT)
