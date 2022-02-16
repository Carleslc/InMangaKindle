#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import re
import math
import json
import signal
import argparse
import tempfile
import bisect
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

import cloudscraper
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

SCRAPER = cloudscraper.create_scraper()

CHAPTERS_FORMAT = 'Format: start..end or chapters with commas. Example: --chapter 3 will download chapter 3, --chapter last will download the last chapter available, --chapters 3..last will download chapters from 3 to the last chapter, --chapter 3 will download only chapter 3, --chapters "3, 12" will download chapters 3 and 12, --chapters "3..12, 15" will download chapters from 3 to 12 and also chapter 15.'

def set_args():
  global args
  parser = argparse.ArgumentParser()
  parser.add_argument("manga", help="manga to download", nargs='+')
  parser.add_argument("--chapters", "--chapter", help=f'chapters to download. {CHAPTERS_FORMAT} If this argument is not provided all chapters will be downloaded.', nargs='+')
  parser.add_argument("--directory", help=f"directory to save downloads. Default: {MANGA_DIR}", default=MANGA_DIR)
  parser.add_argument("--single", action='store_true', help="merge all chapters in only one file. If this argument is not provided every chapter will be in a different file")
  parser.add_argument("--rotate", action='store_true', help="rotate double pages. If this argument is not provided double pages will be splitted in 2 different pages")
  parser.add_argument("--profile", help='Device profile (Available options: K1, K2, K34, K578, KDX, KPW, KV, KO, KoMT, KoG, KoGHD, KoA, KoAHD, KoAH2O, KoAO) [Default = KPW (Kindle Paperwhite)]', default='KPW')
  parser.add_argument("--format", help='Output format (Available options: PNG, PDF, MOBI, EPUB, CBZ) [Default = MOBI]. If PNG is selected then no conversion to e-reader file will be done', default='MOBI')
  parser.add_argument("--fullsize", action='store_true', help="Do not stretch images to the profile's device resolution")
  parser.add_argument("--cache", action='store_true', help="Avoid downloading chapters and use already downloaded chapters instead (offline)")
  parser.add_argument("--remove-alpha", action='store_true', help="When converting to PDF remove alpha channel on images using ImageMagick Wand")
  args = parser.parse_args()

def print_colored(message, *colors, end='\n'):
  def printnoln(s):
    print(s, end='', flush=True)
  for color in colors:
    printnoln(color)
  print(message, end=end)
  printnoln(Style.RESET_ALL)

def error(message, tip=''):
  print_colored(message, Fore.RED, Style.BRIGHT)
  if tip:
    print_dim(tip)
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
  req = SCRAPER.get(url)
  if success(req, text, ok, print_ok=bool(text)):
    data = req.content
    write_file(path, data)
    return True
  return False

def manga_directory(manga):
  return f'{MANGA_DIR}/{manga}'

def chapter_directory(manga, chapter):
  return f'{manga_directory(manga)}/{chapter:g}'

def check_exists_file(path):
  if os.path.isfile(path):
    print_colored(f'{path} - Already exists', Fore.YELLOW)
    return True
  return False
def files(dir, extension=''):
  if not os.path.isdir(dir):
    error(f'{dir} does not exist!')
  def filename(file):
    return file.split('.')[-2]
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

def parse_chapter_intervals(chapter_intervals_str, last, start_end_sep='..', interval_sep=','):
  def parse_chapter(chapter):
    return last if chapter == 'last' else float(chapter)
  
  def parse_chapter_interval(chapter_interval_str):
    boundaries = chapter_interval_str.strip().split(start_end_sep)

    start_chapter = parse_chapter(boundaries[0])
    end_chapter = start_chapter
    
    for chapter in boundaries[1:]:
      chapter = parse_chapter(chapter)
      if chapter < start_chapter:
        start_chapter = chapter
      elif chapter > end_chapter:
        end_chapter = chapter
    
    return start_chapter, end_chapter

  try:
    return merge_intervals(map(parse_chapter_interval, chapter_intervals_str.split(interval_sep)))
  except ValueError:
    error(f'Invalid chapters format', CHAPTERS_FORMAT)

def merge_intervals(chapter_intervals):
  # convert to list and sort intervals by start so overlapping intervals are next to each other
  overlapping_intervals = sorted(chapter_intervals, key=lambda chapter_interval: chapter_interval[0])

  # merge overlapping intervals to remove redundancy

  if len(overlapping_intervals) <= 1:
    return overlapping_intervals

  chapter_intervals = []
  current_start, current_end = overlapping_intervals[0]

  for other_start, other_end in overlapping_intervals[1:]:
    if other_start <= current_end and other_end >= current_start: # overlaps
      current_start = min(current_start, other_start)
      current_end = max(current_end, other_end)
    else:
      chapter_intervals.append((current_start, current_end))
      current_start = other_start
      current_end = other_end
  
  if not chapter_intervals or chapter_intervals[-1][1] != current_end: # last
    chapter_intervals.append((current_start, current_end))
  
  return chapter_intervals

def get_chapter_intervals(sorted_chapters):
  chapter_intervals = [] # list[(start, end)]

  if len(sorted_chapters) > 0:
    start_chapter = sorted_chapters[0]
    end_chapter = start_chapter

    for chapter in sorted_chapters:
      if chapter > end_chapter + 1:
        chapter_intervals.append((start_chapter, end_chapter))
        start_chapter = chapter
      end_chapter = chapter
    
    chapter_intervals.append((start_chapter, end_chapter))
  
  return chapter_intervals

def join_chapter_intervals(chapter_intervals, start_end_sep='..', interval_sep=','):
  def chapter_interval_str(chapter_interval):
    start, end = chapter_interval
    return f'{start:g}{start_end_sep}{end:g}' if start != end else f'{start:g}'
  return interval_sep.join(map(chapter_interval_str, chapter_intervals))

def chapters_to_intervals_string(sorted_chapters, start_end_sep='-', interval_sep=','):
  chapter_intervals = get_chapter_intervals(sorted_chapters)
  return join_chapter_intervals(chapter_intervals, start_end_sep=start_end_sep, interval_sep=interval_sep)

def chapters_in_intervals(sorted_all_chapters, chapter_intervals):
  found_chapters = []
  not_found_chapter_intervals = []

  for start_chapter, end_chapter in chapter_intervals:
    # find index of first chapter available greater or equal than start_chapter
    i = bisect.bisect_left(sorted_all_chapters, start_chapter)
    
    if i < len(sorted_all_chapters):
      chapter = sorted_all_chapters[i]
      in_interval = chapter <= end_chapter
      
      if chapter > start_chapter and in_interval:
        not_found_end_chapter = math.ceil(chapter - 1)
        if not_found_end_chapter < start_chapter:
          not_found_end_chapter = start_chapter
        not_found_chapter_intervals.append((start_chapter, not_found_end_chapter))

      next_int_chapter = None

      # add chapters while they are included in the interval
      while in_interval:
        found_chapters.append(chapter)

        # add chapters in between as not found
        if next_int_chapter is not None and next_int_chapter < chapter:
          not_found_chapter_intervals.append((next_int_chapter, math.ceil(chapter - 1)))
        
        # next chapter
        i += 1
        if i < len(sorted_all_chapters):
          next_int_chapter = math.floor(chapter + 1)
          chapter = sorted_all_chapters[i]
          in_interval = chapter <= end_chapter
        else:
          in_interval = False
      
      # add the interval chapters that cannot be found
      last_chapter_found = found_chapters[-1] if found_chapters else None
      if not found_chapters or last_chapter_found < start_chapter:
        not_found_chapter_intervals.append((start_chapter, end_chapter))
      elif last_chapter_found < end_chapter:
        not_found_start_chapter = math.floor(last_chapter_found + 1)
        if not_found_start_chapter > end_chapter:
          not_found_start_chapter = end_chapter
        not_found_chapter_intervals.append((not_found_start_chapter, end_chapter))
    else:
      not_found_chapter_intervals.append((start_chapter, end_chapter))
  
  if not_found_chapter_intervals:
    not_found_chapter_intervals = merge_intervals(not_found_chapter_intervals)

  return found_chapters, not_found_chapter_intervals

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
  search = SCRAPER.post(SEARCH_URL, data=data, headers=headers)
  exit_if_fails(search)

  return BeautifulSoup(search.content, 'html.parser').find_all("a", href=True, recursive=False)

if __name__ == "__main__":

  cancellable()
  freeze_support()
  init_console_colors()
  
  # PARSE ARGS

  set_args()

  MANGA_DIR = strip_path(args.directory, DIRECTORY_KEEP)

  if not args.profile:
    args.profile = 'KPW'

  MANGA = ' '.join(args.manga)

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
      manga_uuid = manga_href.split('/')[-1]
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
    ALL_CHAPTERS = [float(chapter[0]) for chapter in folders(directory)]
  else:
    chapters_json = SCRAPER.get(CHAPTERS_WEBSITE + manga_uuid)
    exit_if_fails(chapters_json)
    chapters_full = load_json(chapters_json.content, 'data', 'result')
    CHAPTERS_IDS = { float(chapter['Number']): chapter['Identification'] for chapter in chapters_full }
    ALL_CHAPTERS = CHAPTERS_IDS.keys()

  if not ALL_CHAPTERS:
    error(f"There are no chapters of '{manga_title}' available {search_type}")
  
  ALL_CHAPTERS = sorted(ALL_CHAPTERS)

  last = ALL_CHAPTERS[-1]
  
  CHAPTER_INTERVALS = parse_chapter_intervals(' '.join(args.chapters), last) if args.chapters else get_chapter_intervals(ALL_CHAPTERS)

  CHAPTERS, chapters_not_found_intervals = chapters_in_intervals(ALL_CHAPTERS, CHAPTER_INTERVALS)

  if args.cache:
    print_colored(f'Last downloaded chapter: {last:g}', Fore.YELLOW, Style.BRIGHT)
  else:
    print_dim(f'{len(CHAPTERS)} chapter{plural(len(CHAPTERS))} will be downloaded - Cancel with Ctrl+C')

  if chapters_not_found_intervals:
    chapters_not_found_intervals = join_chapter_intervals(chapters_not_found_intervals, interval_sep=', ')
    not_found = 'are not downloaded' if args.cache else 'could not be found'
    print_colored(f'The following chapters {not_found}: {chapters_not_found_intervals}', Fore.RED, Style.BRIGHT)
    if args.cache:
      error(f'Please download those chapters first.', 'Try again this command without --cache')
    else:
      print_colored('🖐️  Press enter to continue without those chapters or Ctrl+C to abort...', Fore.MAGENTA, Style.BRIGHT, end=' ')
      input()
  
  if not CHAPTERS:
    error("No chapters found")

  if not args.cache:
    # DOWNLOAD CHAPTERS

    for chapter in CHAPTERS:
      print_colored(f'Downloading {manga_title} {chapter:g}', Fore.YELLOW, Style.BRIGHT)

      url = CHAPTER_PAGES_WEBSITE + CHAPTERS_IDS[chapter]

      chapter_dir = chapter_directory(manga, chapter)
      page = SCRAPER.get(url)

      if success(page, print_ok=False):
        html = BeautifulSoup(page.content, 'html.parser')
        pages = html.find(id='PageList').find_all(True, recursive=False)
        for page in pages:
          page_id = page.get('value')
          page_number = int(page.get_text())
          url = IMAGE_WEBSITE + page_id
          download(page_number, url, chapter_dir, text=f'Page {page_number}/{len(pages)} ({100*page_number//len(pages)}%)')

  extension = f'.{args.format.lower()}'
  args.format = args.format.upper()

  if args.format != 'PNG':
    print_colored(f'Converting to {args.format}...', Fore.BLUE, Style.BRIGHT)

    if args.format == 'PDF':
      import img2pdf
      if args.remove_alpha:
        import wand.image
      chapters_paths = []
      for chapter in CHAPTERS:
        chapter_dir = chapter_directory(manga, chapter)
        page_number_paths = sorted(list(files(chapter_dir, 'png')), key=lambda page_path: int(page_path[0]))
        page_paths = list(map(lambda page_path: page_path[1], page_number_paths))
        if args.single:
          chapters_paths.extend(page_paths)
        else:
          path = f'{MANGA_DIR}/{manga_title} {chapter:g}{extension}'
          convert_to_pdf(path, page_paths)
      if args.single:
        chapter_interval = chapters_to_intervals_string(CHAPTERS)
        path = f'{MANGA_DIR}/{manga_title} {chapter_interval}{extension}'
        convert_to_pdf(path, chapters_paths)
    else:
      # CONVERT TO E-READER FORMAT
      from kindlecomicconverter.comic2ebook import main as manga2ebook

      argv = ['--output', MANGA_DIR, '-p', args.profile, '--manga-style', '--hq', '-f', args.format, '--batchsplit', single(args.single), '-u', '-r', split_rotate_2_pages(args.rotate)]
      
      if not args.fullsize:
        argv.append('-s')

      if args.single:
        chapter_interval = chapters_to_intervals_string(CHAPTERS)
        with tempfile.TemporaryDirectory() as temp:
          copy_all([(chapter, chapter_directory(manga, chapter)) for chapter in CHAPTERS], temp)
          title = f'{manga_title} {chapter_interval}'
          print_colored(title, Fore.BLUE)
          argv = argv + ['--title', title, temp] # all chapters in manga directory are packed
          cache_convert(argv)
          path = f'{MANGA_DIR}/{manga_title} {chapter_interval}{extension}'
          os.rename(f'{MANGA_DIR}/{os.path.basename(temp)}{extension}', path)
          print_colored(f'DONE: {os.path.abspath(path)}', Fore.GREEN, Style.BRIGHT)
      else:
        for chapter in CHAPTERS:
          title = f'{manga_title} {chapter:g}'
          print_colored(title, Fore.BLUE)
          argv_chapter = argv + ['--title', title, chapter_directory(manga, chapter)]
          cache_convert(argv_chapter)
          path = f'{MANGA_DIR}/{manga_title} {chapter:g}{extension}'
          os.rename(f'{MANGA_DIR}/{chapter:g}{extension}', path)
          print_colored(f'DONE: {os.path.abspath(path)}', Fore.GREEN, Style.BRIGHT)
  else:
    if len(CHAPTERS) == 1:
      directory = os.path.abspath(chapter_directory(manga, CHAPTERS[0]))
      chapter_intervals_info = ''
    else:
      chapter_intervals_info = f" ({chapters_to_intervals_string(CHAPTERS, interval_sep=', ')})"
    print_colored(f'DONE: {directory}{chapter_intervals_info}', Fore.GREEN, Style.BRIGHT)
