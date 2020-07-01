#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import re
import json
import signal
import argparse
import tempfile
from urllib.parse import quote_plus
from multiprocessing import freeze_support

def install_dependencies(dependencies_file):
  # Check dependencies
  import subprocess
  import sys
  from pathlib import Path
  import pkg_resources
  dependencies_path = Path(__file__).with_name(dependencies_file)
  dependencies = pkg_resources.parse_requirements(dependencies_path.open())
  try:
    for dependency in dependencies:
      dependency = str(dependency)
      pkg_resources.require(dependency)
  except pkg_resources.DistributionNotFound as e:
    print("Some dependencies are missing, installing...")
    # Install missing dependencies
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", dependencies_file])

install_dependencies("dependencies.txt")
from requests import get, post
from bs4 import BeautifulSoup
from colorama import Fore, Style, init as init_console_colors

WEBSITE = "https://inmanga.com"
IMAGE_WEBSITE = f"{WEBSITE}/page/getPageImage/?identification="
CHAPTERS_WEBSITE = f"{WEBSITE}/chapter/getall?mangaIdentification="
CHAPTER_PAGES_WEBSITE = f"{WEBSITE}/chapter/chapterIndexControls?identification="
MANGA_WEBSITE = f"{WEBSITE}/ver/manga"

SEARCH_URL = "https://inmanga.com/manga/getMangasConsultResult"

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
  parser.add_argument("--single", action='store_true', help="merge all chapters in only one file. If this argument is not provided every chapter will be in a different file")
  parser.add_argument("--rotate", action='store_true', help="rotate double pages. If this argument is not provided double pages will be splitted in 2 different pages")
  parser.add_argument("--profile", help='Device profile (Available options: K1, K2, K34, K578, KDX, KPW, KV, KO, KoMT, KoG, KoGHD, KoA, KoAHD, KoAH2O, KoAO) [Default = KPW (Kindle Paperwhite)]', default='KPW')
  parser.add_argument("--format", help='Output format (Available options: PNG, PDF, MOBI, EPUB, CBZ) [Default = MOBI]. If PNG is selected then no conversion to e-reader file will be done', default='MOBI')
  parser.add_argument("--fullsize", action='store_true', help="Do not stretch images to the profile's device resolution")
  parser.add_argument("--cache", action='store_true', help="Avoid downloading chapters and use already downloaded chapters instead (offline)")
  parser.add_argument("--remove-alpha", action='store_true', help="When converting to PDF remove alpha channel on images using ImageMagick Wand")
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

def not_found():
  error(f"Manga '{MANGA}' not found")

def print_dim(s, *colors):
  print_colored(s, Style.DIM, *colors)

def print_source(html_soup):
  print_dim(html_soup.prettify())

def cancellable():
  def cancel(s, f):
    print_dim('\nCancelled')
    exit()
  try:
    signal.signal(signal.SIGINT, cancel)
  except:
    pass

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

def encode(title):
  return re.sub(r'\W+', '-', title)

def decode(title):
  return title.replace('-', ' ')

def plural(size):
  return 's' if size != 1 else ''

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

def check_exists_dir(path):
  if not os.path.isdir(path):
    tip = ' Try again this command without --cache' if args.cache else ''
    error(f'{path} is not downloaded, please download that chapter first.{tip}');

def files(dir, extension=''):
  def filename(file):
    return file.split('.')[-2]
  check_exists_dir(dir)
  for file in os.listdir(dir):
    path = os.path.abspath(f'{dir}/{file}')
    if os.path.isfile(path) and file.endswith(extension):
      yield filename(file), path

def folders(dir):
  if not os.path.isdir(dir):
    error(f'{dir} does not exist');
  for subdir in os.listdir(dir):
    path = os.path.abspath(f'{dir}/{subdir}')
    if os.path.isdir(path):
      yield subdir, path

def copy_all(name_path_list, to_path):
  import errno, shutil
  def copy(src, dest):
    try:
      shutil.copytree(src, dest)
    except OSError as e:
      if e.errno == errno.ENOTDIR: # src is file
        shutil.copy(src, dest)
      else:
        error(e)
  for name, path in name_path_list:
    copy(path, f'{to_path}/{name}')

def load_json(data, *keys):
  data = json.loads(data)
  for key in keys[:-1]:
    data = json.loads(data.get(key))
  return data.get(keys[-1])

def parse_chapters_range(chapters, last):
  global CHAPTERS

  def get_number(number):
    return last if number == 'last' else int(number)

  ranges = chapters.split(',')
  try:
    for r in ranges:
      split = r.split('..')
      if len(split) == 1:
        CHAPTERS.add(get_number(split[0]))
      else:
        CHAPTERS.update(range(get_number(split[0]), get_number(split[1]) + 1))
  except ValueError:
    error('Invalid chapters format')

def filename_chapter_range():
  min_chapter = min(CHAPTERS)
  max_chapter = max(CHAPTERS)
  return str(min_chapter) if min_chapter == max_chapter else f'{min_chapter}-{max_chapter}'

def split_rotate_2_pages(rotate):
  return str(1 if rotate else 0)

def single(single):
  return str(0 if single else 2)

def removeAlpha(image_path):
  with wand.image.Image(filename=image_path) as img:
    if img.alpha_channel:
      img.alpha_channel = 'remove'
      img.background_color = wand.image.Color('white')    
      img.save(filename=image_path)

def convert_to_pdf(path, chapters_paths):
  if not check_exists_file(path):
    if args.remove_alpha:
      print_dim(f'Removing alpha channel from images for {path}')
      for img_path in chapters_paths:
        removeAlpha(img_path)
    with open(path, "wb") as f:
      f.write(img2pdf.convert(chapters_paths))
    print_colored(f'DONE: {os.path.abspath(path)}', Fore.GREEN, Style.BRIGHT)

def fix_corrupted_file(corrupted_file, corrupted_file_path, argv):
  print_colored(f'{corrupted_file} is corrupted, removing and trying again... (Cancel with Ctrl+C)', Fore.RED)
  local_corrupted_file_path = os.path.abspath(f'{directory}/{corrupted_file}')
  print_dim(local_corrupted_file_path)
  os.remove(local_corrupted_file_path)
  if corrupted_file_path != local_corrupted_file_path:
    os.remove(corrupted_file_path)
  cache_convert(argv)

def convert_except(e, argv):
  message = str(e)
  corrupted_file_path = re.findall(r'Image file (.*?) is corrupted', message)
  if len(corrupted_file_path) > 0:
    parts = corrupted_file_path[0].split('/')
    corrupted_file = f'{parts[-2]}/{parts[-1]}'
    fix_corrupted_file(corrupted_file, os.path.abspath(corrupted_file_path[0]), argv)
  else:
    import traceback
    traceback.print_tb(e.__traceback__)
    error(e)

def cache_convert(argv):
  try:
    manga2ebook(argv)
  except Exception as e:
    convert_except(e, argv)

def online_search():
  data = {
    'hfilter[generes][]': '-1',
    'filter[queryString]': MANGA,
    'filter[skip]': '0',
    'filter[take]': '10',
    'filter[sortby]': '1',
    'filter[broadcastStatus]': '0',
    'filter[onlyFavorites]': 'false'
  }

  headers = {
    'Origin': 'https://inmanga.com',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Accept': '*/*',
    'Referer': 'https://inmanga.com/manga/consult?suggestion=' + MANGA,
    'X-Requested-With': 'XMLHttpRequest'
  }

  # Alternative Search: https://inmanga.com/OnMangaQuickSearch/Source/QSMangaList.json
  search = post(SEARCH_URL, data=data, headers=headers)
  exit_if_fails(search)

  return BeautifulSoup(search.content, 'html.parser').find_all("a", href=True, recursive=False)

if __name__ == "__main__":

  cancellable()
  init_console_colors()
  
  # PARSE ARGS

  set_args()

  MANGA_DIR = strip_path(args.directory, DIRECTORY_KEEP)

  CHAPTERS = set()

  if not args.profile:
    args.profile = 'KPW'

  MANGA = args.manga

  # SEARCH ANIME

  search_type = f'in {MANGA_DIR}' if args.cache else 'online'
  print_colored(f"Searching '{MANGA}' {search_type}...", Style.BRIGHT)

  results = []
  match = False
  if args.cache: # offline search
    encoded_title = encode(MANGA).upper()
    for cached in folders(MANGA_DIR):
      manga = cached[0]
      encoded_cached = manga.upper()
      manga_title = decode(manga)
      if encoded_title == encoded_cached:
        match = True
        break
      elif encoded_cached in encoded_title or encoded_title in encoded_cached:
        results.append(manga_title)
        submatch_manga = manga
  else: # online search
    for result in online_search():
      manga_href = result.get('href')
      if manga_href is None:
        not_found()
      manga = manga_href.split('/')[-2] # encoded title
      uuid = manga_href.split('/')[-1]
      manga_title = result.find('h4').get_text().strip() # may contain special characters
      if manga_title.upper() == MANGA.upper():
        match = True
        break
      results.append(manga_title)

  if not match:
    if len(results) > 1:
      upper_titles = [title.upper() for title in results]
      error('There are several results, please select one of these:\n' + '\n'.join(upper_titles))
    elif len(results) == 1:
      manga_title = results[0]
      if args.cache:
        manga = submatch_manga
    else:
      not_found()

  print_colored(manga_title, Fore.BLUE)

  # RETRIEVE CHAPTERS

  directory = os.path.abspath(manga_directory(manga))

  if args.cache:
    all_chapters = [int(chapter[0]) for chapter in folders(directory)]
  else:
    chapters_json = get(CHAPTERS_WEBSITE + uuid)
    exit_if_fails(chapters_json)
    chapters_full = load_json(chapters_json.content, 'data', 'result')
    all_chapters = [int(chapter['Number']) for chapter in chapters_full]

  last = max(all_chapters)
  if args.cache:
    print_colored(f'Last downloaded chapter: {last}', Fore.YELLOW, Style.BRIGHT);

  if args.chapters:
    args.chapters = args.chapters.replace(' ', '')
    parse_chapters_range(args.chapters, last)
  else:
    CHAPTERS.update(all_chapters)

  if args.cache:
    for chapter in CHAPTERS:
      check_exists_dir(chapter_directory(manga, chapter))
  else:
    # DOWNLOAD CHAPTERS

    uuids = {}
    for chapter in chapters_full:
      number = chapter['Number']
      if number in CHAPTERS:
        uuids[number] = chapter['Identification']

    CHAPTERS = sorted(CHAPTERS)
    print_dim(f'{len(CHAPTERS)} chapter{plural(len(CHAPTERS))} will be downloaded - Cancel with Ctrl+C')

    if not args.cache:
      downloaded = False

      for chapter in CHAPTERS:
        uuid = uuids.get(chapter)
        if uuid is None:
          print_colored(f'{manga_title} {chapter} not found', Fore.RED)
        else:
          print_colored(f'Downloading {manga_title} {chapter}', Fore.YELLOW, Style.BRIGHT)

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
  args.format = args.format.upper()

  chapter_range = args.chapters.replace('last', str(last)) if args.chapters else filename_chapter_range()

  if args.format != 'PNG':
    print_colored(f'Converting to {args.format}...', Fore.BLUE, Style.BRIGHT)

    if args.format == 'PDF':
      import img2pdf
      if args.remove_alpha:
        import wand.image
      chapters_paths = []
      for chapter in CHAPTERS:
        chapter_dir = chapter_directory(manga, chapter)
        page_number_paths = sorted(list(files(chapter_dir, 'png')), key=lambda name_path: int(name_path[0]))
        page_paths = list(map(lambda name_path: name_path[1], page_number_paths))
        if args.single:
          chapters_paths.extend(page_paths)
        else:
          path = f'{MANGA_DIR}/{manga_title} {chapter}{extension}'
          convert_to_pdf(path, page_paths)
      if args.single:
        path = f'{MANGA_DIR}/{manga_title} {chapter_range}{extension}'
        convert_to_pdf(path, chapters_paths)
    else:
      # CONVERT TO E-READER FORMAT
      from kindlecomicconverter.comic2ebook import main as manga2ebook

      freeze_support()

      argv = ['--output', MANGA_DIR, '-p', args.profile, '--manga-style', '--hq', '-f', args.format, '--batchsplit', single(args.single), '-u', '-r', split_rotate_2_pages(args.rotate)]
      
      if not args.fullsize:
        argv.append('-s')

      if args.single:
        with tempfile.TemporaryDirectory() as temp:
          copy_all([(chapter, chapter_directory(manga, chapter)) for chapter in CHAPTERS], temp)
          title = f'{manga_title} {chapter_range}'
          print_colored(title, Fore.BLUE)
          argv = argv + ['--title', title, temp] # all chapters in manga directory are packed
          cache_convert(argv)
          path = f'{MANGA_DIR}/{manga_title} {chapter_range}{extension}'
          os.rename(f'{MANGA_DIR}/{os.path.basename(temp)}{extension}', path)
          print_colored(f'DONE: {os.path.abspath(path)}', Fore.GREEN, Style.BRIGHT)
      else:
        for chapter in CHAPTERS:
          title = f'{manga_title} {chapter}'
          print_colored(title, Fore.BLUE)
          argv_chapter = argv + ['--title', title, chapter_directory(manga, chapter)]
          cache_convert(argv_chapter)
          path = f'{MANGA_DIR}/{manga_title} {chapter}{extension}'
          os.rename(f'{MANGA_DIR}/{chapter}{extension}', path)
          print_colored(f'DONE: {os.path.abspath(path)}', Fore.GREEN, Style.BRIGHT)
  else:
    print_colored(f'DONE: {directory}', Fore.GREEN, Style.BRIGHT)
