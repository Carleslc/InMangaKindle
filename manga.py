#!/usr/bin/python3
# -*- coding: utf-8 -*-

VERSION = '1.8'

NAME = 'InMangaKindle'
WEBSITE = 'https://carleslc.me/InMangaKindle/'

SUPPORT_PYTHON = [(3,6,0), (3,14,0)]
RECOMMENDED_PYTHON = 'https://www.python.org/downloads/latest/python3.13/'

FORMATS = ['PNG', 'PDF', 'EPUB', 'MOBI', 'CBZ', 'KFX', 'MOBI+EPUB']
DEFAULT_FORMAT = 'EPUB'
DEFAULT_PROFILE = 'KPW'

import os
import re
import sys
import math
import json
import signal
import argparse
import tempfile
import bisect
import platform
import subprocess
from multiprocessing import freeze_support

DEPENDENCIES_FILE = "dependencies.txt"

def check_dependencies(dependencies_file):
  '''Install dependencies if not installed'''
  from pathlib import Path
  try:
    from importlib.metadata import distribution, PackageNotFoundError
  except ImportError:
    # Fallback for Python < 3.8
    from importlib_metadata import distribution, PackageNotFoundError  # pyright: ignore[reportMissingImports]
  try:
    from packaging.requirements import Requirement
    
    dependencies_path = Path(__file__).with_name(dependencies_file)
    with dependencies_path.open() as f:
      dependencies = [Requirement(line.strip()) for line in f if line.strip() and not line.strip().startswith('#')]
    
    if sys.version_info >= (3, 8):
      dependencies = [dependency for dependency in dependencies if dependency.name != 'importlib-metadata']
    
    for dependency in dependencies:
      # Check if the package is installed
      distribution(dependency.name)
  except (PackageNotFoundError, ImportError):
    print("Some dependencies are missing, installing...")
    # Install missing dependencies
    install_dependencies(dependencies_file)

def install_dependencies(dependencies_file, update=False):
  try:
    install_command = [sys.executable, "-m", "pip", "install"]
    if update:
      install_command.extend(["--upgrade", "--force-reinstall", "--no-deps"])
    install_command.append("-r")
    install_command.append(dependencies_file)
    subprocess.check_call(install_command)
  except subprocess.CalledProcessError as e:
    error(f"Failed to install dependencies: {e}")

check_dependencies(DEPENDENCIES_FILE)

import requests
import cloudscraper
from bs4 import BeautifulSoup
from colorama import Fore, Style, init as init_console_colors

PROVIDER_WEBSITE = "https://inmanga.com"
IMAGE_CDN = "https://cdn1.intomanga.com/i/m"
CHAPTERS_WEBSITE = f"{PROVIDER_WEBSITE}/chapter/getall?mangaIdentification="
CHAPTER_PAGES_WEBSITE = f"{PROVIDER_WEBSITE}/chapter/chapterIndexControls?identification="
MANGA_WEBSITE = f"{PROVIDER_WEBSITE}/ver/manga"

SEARCH_URL = "https://inmanga.com/manga/getMangasConsultResult"

MANGA_DIR = './manga'

PATH_SEPARATORS = set(['/', '\\'])

FILENAME_KEEP = set(['_', '-', ' ', '.'])
DIRECTORY_KEEP = FILENAME_KEEP | PATH_SEPARATORS
EXTENSION_KEEP = set('.')

SCRAPER = cloudscraper.create_scraper()

CHAPTERS_FORMAT = 'Format: start..end or chapters with commas. Example: --chapter 3 will download chapter 3, --chapter last will download the last chapter available, --chapters 3..last will download chapters from 3 to the last chapter, --chapter 3 will download only chapter 3, --chapters "3, 12" will download chapters 3 and 12, --chapters "3..12, 15" will download chapters from 3 to 12 and also chapter 15.'

def set_args():
  global args
  parser = argparse.ArgumentParser(epilog=f'web: {WEBSITE}')
  parser.add_argument("manga", help="manga to download", nargs='+')
  parser.add_argument("--chapters", "--chapter", help=f'chapters to download. {CHAPTERS_FORMAT} If this argument is not provided all chapters will be downloaded.', nargs='+')
  parser.add_argument("--directory", help=f"directory to save downloads. Default: {MANGA_DIR}", default=MANGA_DIR)
  parser.add_argument("--single", action='store_true', help="merge all chapters in only one file. If this argument is not provided every chapter will be in a different file")
  parser.add_argument("--rotate", action='store_true', help="rotate double pages. If this argument is not provided double pages will be splitted in 2 different pages")
  parser.add_argument("--profile", help=f'Device profile (Use --profiles to list available profiles) [Default = {DEFAULT_PROFILE} (Kindle Paperwhite 1/2)]', default=DEFAULT_PROFILE)
  parser.add_argument("--profiles", action=ListProfiles, help="List available device profiles from Kindle Comic Converter")
  parser.add_argument("--format", help=f"Output format (Available options: {', '.join(FORMATS)}) [Default = {DEFAULT_FORMAT}]. If PNG is selected then no conversion to e-reader file will be done", default=DEFAULT_FORMAT)
  parser.add_argument("--fullsize", action='store_true', help="Do not stretch images to the profile's device resolution")
  parser.add_argument("--color", action='store_true', help="Don't convert images to grayscale")
  parser.add_argument("--cache", action='store_true', help="Avoid downloading chapters and use already downloaded chapters instead (offline)")
  parser.add_argument("--remove-alpha", action='store_true', help="Remove images transparency (alpha channel)")
  parser.add_argument("--update", action=InstallDependencies, help="Update dependencies to the latest version")
  parser.add_argument("--version", "-v", action=CheckVersion, help="Display current InMangaKindle version", version=VERSION)
  args = parser.parse_args()

class InstallDependencies(argparse.Action):
  def __init__(self, option_strings, **kwargs):
    super(InstallDependencies, self).__init__(option_strings, nargs=0, **kwargs)
  def __call__(self, parser, namespace, values, option_string=None):
    init_console_colors()
    check_version()
    update_dependencies()
    exit()

def update_dependencies():
  print_colored("Updating dependencies...", Fore.YELLOW)
  install_dependencies(DEPENDENCIES_FILE, update=True)

class CheckVersion(argparse.Action):
  def __init__(self, option_strings, version=VERSION, **kwargs):
    super(CheckVersion, self).__init__(option_strings, nargs=0, **kwargs)
    self.version = version
  def __call__(self, parser, namespace, values, option_string=None):
    init_console_colors()
    print_colored(NAME, Style.BRIGHT, end=' ')
    print_colored(self.version, Style.BRIGHT, Fore.CYAN)
    if check_version():
      print_colored('✅ Up to date', Fore.GREEN)
    exit()

class ListProfiles(argparse.Action):
  def __init__(self, option_strings, **kwargs):
    super(ListProfiles, self).__init__(option_strings, nargs=0, **kwargs)
  def __call__(self, parser, namespace, values, option_string=None):
    try:
      init_console_colors()
      from kindlecomicconverter.image import ProfileData
      
      all_profiles = getattr(ProfileData, 'Profiles', {})
      kindle_profiles = getattr(ProfileData, 'ProfilesKindle', {})
      kobo_profiles = getattr(ProfileData, 'ProfilesKobo', {})
      remarkable_profiles = getattr(ProfileData, 'ProfilesRemarkable', {})
      other_profiles = {k: v for k, v in all_profiles.items() if k not in kindle_profiles and k not in kobo_profiles and k not in remarkable_profiles}
      
      def print_profiles(profiles_dict, category_name):
        if profiles_dict:
          print_colored(f'\n{category_name}', Fore.BLUE, Style.BRIGHT)
          for profile in sorted(profiles_dict.keys()):
            device_name = profiles_dict[profile][0]
            print_colored(profile, Fore.CYAN, end='\t')
            print(device_name)

      print_dim('Available device profiles:')
      
      print_profiles(kindle_profiles, 'Kindle')
      print_profiles(kobo_profiles, 'Kobo')
      print_profiles(remarkable_profiles, 'reMarkable')
      print_profiles(other_profiles, 'Other')

      print_colored('\nDefault:', Fore.CYAN, Style.BRIGHT, end=' ')
      print_colored('--profile', end=' ')
      print_colored(DEFAULT_PROFILE, Fore.CYAN, Style.BRIGHT)

      print_colored('Usage:', Fore.GREEN, Style.BRIGHT, end=' ')
      print_colored('python manga.py', end=' ')
      print_colored('--profile', Fore.CYAN, end=' ')
      print_colored('KO', Fore.CYAN, Style.BRIGHT)
    except ImportError:
      error('Kindle Comic Converter is not installed. Please install dependencies first.', 'Run: python manga.py --update')
    exit()

def check_version():
  if not is_python_version_supported():
    print_colored(python_not_supported(), Fore.RED)
  latest_version = None
  try:
    response = requests.get(f'https://api.github.com/repos/Carleslc/{NAME}/releases/latest')
    html_url = load_json(response.content, 'html_url')
    latest_version = load_json(response.content, 'tag_name')
  except:
    if not args.cache:
      print_dim(f'Cannot check for updates. Version: {VERSION}', Fore.YELLOW)
  if latest_version is None:
    return False
  is_updated = latest_version == VERSION
  if not is_updated:
    print_colored(f'New version is available! {VERSION} -> {latest_version}', Style.BRIGHT, Fore.GREEN)
    print_colored(f'Upgrade to the latest version: {html_url}', Fore.GREEN)
    if os.path.isdir('.git'):
      print_colored('Git detected. Do you want to checkout the new version❓ [Y/n]', Fore.YELLOW, Style.BRIGHT, end=' ')
      answer = input()
      if not answer or answer.lower() == 'y':
        try:
            subprocess.check_call(['git', 'fetch', '--tags', 'origin'])
            subprocess.check_call(['git', 'checkout', latest_version])
            print_colored('Updated to the latest version', Fore.GREEN, end=' ')
            print_colored(latest_version, Style.BRIGHT, Fore.CYAN)
            update_dependencies()
            print_colored(f'Run {NAME} again to use the latest version', Fore.YELLOW, Style.BRIGHT)
            exit()
        except subprocess.CalledProcessError as e:
          error(f'Failed to update: {e}', halt=False)
      print('If you want to update later manually use ', end='')
      print_colored(f'git fetch --tags && git checkout {latest_version}', Fore.YELLOW)
  return is_updated

def is_python_version_supported():
  min_version, max_version = SUPPORT_PYTHON
  major, minor, _ = platform.python_version_tuple()
  major = int(major)
  minor = int(minor)
  return major >= min_version[0] and minor >= min_version[1] and major <= max_version[0] and minor <= max_version[1]

def python_not_supported():
  min_version, max_version = SUPPORT_PYTHON
  min_version = '.'.join(map(str, min_version))
  max_version = '.'.join(map(str, max_version))
  return f'Your Python version {platform.python_version()} may not be fully supported ({sys.executable} --version). Please, use a Python version between {min_version} and {max_version}\n{RECOMMENDED_PYTHON}'

def print_colored(message, *colors, end='\n'):
  def printnoln(s):
    print(s, end='', flush=True)
  for color in colors:
    printnoln(color)
  print(message, end=end)
  printnoln(Style.RESET_ALL)

def error(message, tip='', halt=True):
  print_colored(message, Fore.RED, Style.BRIGHT)
  if tip:
    print_dim(tip)
  if halt:
    exit()

def not_found():
  error(f"Manga '{MANGA}' not found")

def print_dim(s, *colors, end='\n'):
  print_colored(s, Style.DIM, *colors, end=end)

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

def network_error(message=None):
  error_message = 'Network error'
  if message:
    error_message = f'{error_message}: {message}'
  tip = 'Are you connected to Internet?'
  if not args.cache:
    tip += '\nYou can use offline mode (using your already downloaded chapters) with --cache'
  error(error_message, tip)

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

def strip_name(name, keep=FILENAME_KEEP):
  return ''.join(c for c in name if c.isalnum() or c in keep).strip()

def strip_path(path, keep=DIRECTORY_KEEP):
  # Sanitize every path component separately, preserving path separators and the drive (Windows: C:\)
  # Both '/' and '\' are treated as separators, so os.path.join results are handled correctly on POSIX and Windows
  keep = set(keep) - PATH_SEPARATORS
  drive, tail = os.path.splitdrive(path)
  parts = re.split(r'[\\/]', tail)
  parts = [part if part in ('', os.curdir, os.pardir) else strip_name(part, keep) for part in parts]
  return drive + os.sep.join(parts)

def encode_path(filename, extension, directory='.'):
  return strip_path(os.path.join(directory, filename), DIRECTORY_KEEP) + '.' + strip_name(extension, EXTENSION_KEEP)

def encode(title):
  return re.sub(r'\W+', '-', title)

def decode(title):
  return title.replace('-', ' ')

def plural(size):
  return 's' if size != 1 else ''

def download(filename, url, directory='.', extension='png', text='', ok=200, referer=None):
  path = encode_path(filename, extension, directory)

  # Check if file already exists
  if os.path.isfile(path):
    if os.path.getsize(path) > 0:
      text = text if text else path
      separation = ' ' * (20 - len(text))
      print_colored(f'{text}{separation}- Already exists', Fore.YELLOW)
      return False
    # Empty/corrupted file (download again)
    os.remove(path)

  headers = {
    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    'Sec-Fetch-Dest': 'image',
    'Sec-Fetch-Mode': 'no-cors',
    'Sec-Fetch-Site': 'same-origin',
    'Upgrade-Insecure-Requests': '1'
  }
  if referer:
    headers['Referer'] = referer

  req = SCRAPER.get(url, headers=headers, allow_redirects=True)
  data = req.content

  if len(data) == 0:
    print_colored(f'{text if text else path} - Empty response from server', Fore.RED)
    return False

  if success(req, text, ok, print_ok=bool(text)):
    write_file(path, data)
    return True
  return False

def manga_directory(manga):
  return os.path.join(MANGA_DIR, manga)

def chapter_directory(manga, chapter):
  return os.path.join(MANGA_DIR, manga, f'{chapter:g}')

def output_filename_path(title='', chapter_interval=None, extension=None):
  if isinstance(chapter_interval, float):
    chapter_interval = f'{chapter_interval:g}'
  elif isinstance(chapter_interval, list):
    chapter_interval = chapters_to_intervals_string(chapter_interval)
  filename = title
  if chapter_interval is not None:
    filename += f' {chapter_interval}' if title else chapter_interval
  extension = '.' + extension if extension else ''
  path = os.path.join(MANGA_DIR, filename + extension)
  return filename, path

def output_path(title='', chapter_interval=None, extension=None):
  _, path = output_filename_path(title, chapter_interval, extension)
  return path

def done(path):
  print_colored(f'DONE: {os.path.abspath(path)}', Fore.GREEN, Style.BRIGHT)

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
    path = os.path.abspath(os.path.join(dir, file))
    if os.path.isfile(path) and file.endswith(extension):
      yield filename(file), path

def folders(dir):
  if not os.path.isdir(dir):
    error(f'{dir} does not exist');
  for subdir in os.listdir(dir):
    path = os.path.abspath(os.path.join(dir, subdir))
    if os.path.isdir(path):
      yield subdir, path

def copy_all(path_list, to_path):
  import errno, shutil
  def copy(src, dest):
    try:
      shutil.copytree(src, dest)
    except OSError as e:
      if e.errno == errno.ENOTDIR: # src is file
        shutil.copy(src, dest)
      else:
        error(e)
  for path in path_list:
    name = os.path.basename(path)
    copy(path, os.path.join(to_path, name))

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

def format_extension(format):
  if format == 'KFX':
    # https://github.com/ciromattia/kcc/blob/v9.4.1/kindlecomicconverter/comic2ebook.py#L1466
    return 'epub'
  elif format == 'MOBI+EPUB':
    return 'mobi'
  return format.lower()

def validate_chapter_images(chapters, manga, manga_title):
    def has_images(chapter):
      chapter_dir = chapter_directory(manga, chapter)
      if not os.path.isdir(chapter_dir):
        return False
      for img in os.listdir(chapter_dir):
        if img.endswith('.png'):
          path = os.path.join(chapter_dir, img)
          if os.path.isfile(path) and os.path.getsize(path) > 0:
            return True
      return False

    skip_chapters = []
    chapters_with_images = []

    for chapter in chapters:
      include_to = chapters_with_images if has_images(chapter) else skip_chapters
      include_to.append(chapter)

    if not chapters_with_images:
      if args.cache:
        message = 'Please download chapters images first.'
        tip = 'Try again this command without --cache'
      else:
        message = f'This may be due to:\n- Network issues\n- Chapter not available\n- API changes on {PROVIDER_WEBSITE}'
        tip = f'Try checking the chapter availability on {PROVIDER_WEBSITE} or try again later.'
      error(f'No images were downloaded. {message}', tip)
    
    if skip_chapters:
      for chapter in skip_chapters:
        print_colored(f'Skipping {manga_title} {chapter:g} - no images downloaded', Fore.YELLOW)
    
    return chapters_with_images

def removeAlpha(image_path):
  try:
    # Pillow
    from PIL import Image
    with Image.open(image_path) as img:
      if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        img_rgba = img.convert("RGBA")
        alpha = img_rgba.split()[-1]
        new_img = Image.new("RGB", img_rgba.size, (255, 255, 255))
        new_img.paste(img_rgba, mask=alpha)
        new_img.save(image_path, "PNG")
    return True
  except:
    try:
      # Wand + ImageMagick
      # https://docs.wand-py.org/en/stable/guide/install.html
      import wand.image
      with wand.image.Image(filename=image_path) as img:
        if img.alpha_channel:
          img.alpha_channel = 'remove'
          img.background_color = wand.image.Color('white')    
          img.save(filename=image_path)
      return True
    except:
      return False

def convert_to_pdf(title, path_pdf, pages_paths):
  if not check_exists_file(path_pdf):
    import img2pdf
    def img2pdf_convert():
      with open(path_pdf, 'wb') as f:
        f.write(img2pdf.convert(pages_paths))
    print_colored(title, Fore.BLUE)
    try:
      img2pdf_convert()
    except img2pdf.AlphaChannelError:
      print_colored('Image transparency detected (not supported by PDF). Attempting to remove alpha channel automatically...', Fore.YELLOW)
      for img_path in pages_paths:
        removeAlpha(img_path)
      try:
        img2pdf_convert()
      except img2pdf.AlphaChannelError:
        error('Some images have an alpha channel which could not be removed automatically.', 'Try installing ImageMagick (Wand) or use a different --format.\nhttps://docs.wand-py.org/en/stable/guide/install.html')
    done(path_pdf)

def fix_corrupted_file(corrupted_file, corrupted_file_path, argv):
  print_colored(f'{corrupted_file} is corrupted or missing, removing and trying again... (Cancel with Ctrl+C)', Fore.RED)
  if os.path.exists(corrupted_file_path):
    print_dim(corrupted_file_path)
    os.remove(corrupted_file_path)
  # Remove from manga directory (if corrupted file was in --single temporal directory)
  local_path = os.path.abspath(os.path.join(directory, corrupted_file))
  if local_path != corrupted_file_path and os.path.exists(local_path):
    os.remove(local_path)
  # Try to convert again without the corrupted file
  cache_convert(argv)

def convert_except(e, argv):
  message = str(e)
  corrupted_file_match = re.search(r'Image file (.*?) is corrupted', message)
  if corrupted_file_match:
    corrupted_file_path = corrupted_file_match.group(1)
    parts = re.split(r'[\\/]', corrupted_file_path)
    corrupted_file = os.path.join(*parts[-2:])
    fix_corrupted_file(corrupted_file, os.path.abspath(corrupted_file_path), argv)
  elif message.startswith('("One of workers crashed. Cause: \'float\' object cannot be interpreted as an integer"'):
    tip = 'https://github.com/Carleslc/InMangaKindle/issues/13'
    python_supported = is_python_version_supported()
    if not python_supported:
      tip = python_not_supported() + '\n' + tip
    error(tip, message)
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

  try:
    # Alternative Search: https://inmanga.com/OnMangaQuickSearch/Source/QSMangaList.json
    search = SCRAPER.post(SEARCH_URL, data=data, headers=headers, timeout=30)
    exit_if_fails(search)
  except requests.exceptions.Timeout:
    network_error(f'Timeout while searching on {PROVIDER_WEBSITE}')
  except requests.exceptions.ConnectionError:
    network_error(f'Connection error while searching on {PROVIDER_WEBSITE}')

  return BeautifulSoup(search.content, 'html.parser').find_all("a", href=True, recursive=False)

if __name__ == "__main__":

  cancellable()
  freeze_support()
  init_console_colors()
  
  # PARSE ARGS

  set_args()

  MANGA_DIR = strip_path(args.directory, DIRECTORY_KEEP)

  MANGA = ' '.join(args.manga)

  check_version()

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
    try:
      chapters_json = SCRAPER.get(CHAPTERS_WEBSITE + manga_uuid)
      exit_if_fails(chapters_json)
    except requests.exceptions.ConnectionError:
      network_error(f'Connection error while retrieving chapters from {PROVIDER_WEBSITE}')
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
      error('Please download those chapters first.', 'Try again this command without --cache')
    else:
      print_colored('🖐️  Press enter to continue without those chapters or Ctrl+C to abort...', Fore.MAGENTA, Style.BRIGHT, end=' ')
      input()
  
  if not CHAPTERS:
    error("No chapters found")

  if not args.cache:
    # DOWNLOAD CHAPTERS

    for chapter in CHAPTERS:
      print_colored(f'Downloading {manga_title} {chapter:g}', Fore.YELLOW, Style.BRIGHT)

      chapter_url = CHAPTER_PAGES_WEBSITE + CHAPTERS_IDS[chapter]

      chapter_dir = chapter_directory(manga, chapter)
      try:
        page = SCRAPER.get(chapter_url)

        if success(page, print_ok=False):
          html = BeautifulSoup(page.content, 'html.parser')
          pages = html.find(id='PageList').find_all(True, recursive=False)
          
          chapter_id_input = html.find('input', {'id': 'ChapterIdentification'})
          chapter_uuid = chapter_id_input.get('value') if chapter_id_input else CHAPTERS_IDS[chapter].lower()
          
          chapter_number_input = html.find('input', {'id': 'ChapterNumber'})
          chapter_number_id = chapter_number_input.get('value') if chapter_number_input else f"{chapter:,}"
          
          chapter_url = f"{MANGA_WEBSITE}/{manga}/{chapter_number_id}/{chapter_uuid}"

          print_dim(chapter_url)
          
          # Download chapter images
          i = 1
          for page in pages:
            page_id = page.get('value')
            page_number = page.get_text()
            image_url = f"{IMAGE_CDN}/{manga_uuid}/c/{chapter_uuid}/o/{page_id}.jpg"
            download(page_number, image_url, chapter_dir, text=f'Page {i}/{len(pages)} ({100*i//len(pages)}%)', referer=chapter_url)
            i += 1
      except requests.exceptions.ConnectionError:
        network_error(f'Connection error while downloading chapter images from {chapter_url}')

  args.format = args.format.upper()

  if args.format not in FORMATS:
    error(f'Invalid format: {args.format}', f"Available formats: {', '.join(FORMATS)}", halt=False)
    args.format = DEFAULT_FORMAT

  extension = format_extension(args.format)

  CHAPTERS = validate_chapter_images(CHAPTERS, manga, manga_title)

  chapters_image_paths = {}

  if args.remove_alpha or args.format == 'PDF':
    for chapter in CHAPTERS:
      chapter_dir = chapter_directory(manga, chapter)
      page_number_paths = sorted(list(files(chapter_dir, 'png')), key=lambda page_path: int(page_path[0]))
      page_paths = list(map(lambda page_path: page_path[1], page_number_paths))
      chapters_image_paths[chapter] = page_paths

  if args.remove_alpha:
    print_colored('Removing transparency from images...', Fore.YELLOW)
    for chapter in CHAPTERS:
      for img_path in chapters_image_paths[chapter]:
        removeAlpha(img_path)

  if args.format != 'PNG':
    print_colored(f'Converting to {args.format}...', Fore.BLUE, Style.BRIGHT)

    if args.format == 'PDF':
      # CONVERT TO PDF
      if args.single:
        all_pages_paths = [pages_paths for chapter in CHAPTERS for pages_paths in chapters_image_paths[chapter]]
        title, path = output_filename_path(manga_title, CHAPTERS, extension)
        convert_to_pdf(title, path, all_pages_paths)
      else:
        for chapter in CHAPTERS:
          pages_paths = chapters_image_paths[chapter]
          title, path = output_filename_path(manga_title, chapter, extension)
          convert_to_pdf(title, path, pages_paths)
    else:
      # CONVERT TO E-READER FORMAT
      from kindlecomicconverter.comic2ebook import main as manga2ebook
      from kindlecomicconverter.image import ProfileData

      if args.format == 'KFX':
        print_colored('KFX output creates EPUB that can be converted to KFX by jhowell KFX Output Calibre plugin', Fore.YELLOW)
        print_dim('https://www.mobileread.com/forums/showthread.php?t=272407')
      
      profiles = getattr(ProfileData, 'Profiles', {})

      if args.profile not in profiles:
        error(f'Invalid device profile: {args.profile}', 'Use --profiles to list available profiles', halt=False)
        args.profile = DEFAULT_PROFILE

      profile_name = profiles[args.profile][0]

      print_dim('Profile:', end=' ')
      print_colored(f"{args.profile} ({profile_name})", Fore.CYAN)

      # https://github.com/ciromattia/kcc?tab=readme-ov-file#standalone-kcc-c2epy-usage
      argv = [
        '--author', NAME,
        '--output', MANGA_DIR,
        '--profile', args.profile,
        '--format', args.format,
        '--batchsplit', single(args.single),
        '--splitter', split_rotate_2_pages(args.rotate),
        '--manga-style',
        '--hq',
        '--upscale',
      ]
      
      if not args.fullsize:
        argv.append('--stretch')
      
      if args.color:
        argv.append('--forcecolor')

      def convert_to_ereader(title, path, src_chapter, src_dir):
        print_colored(title, Fore.BLUE)
        argv_convert = argv + ['--title', title, src_dir]
        cache_convert(argv_convert)
        os.rename(output_path(chapter_interval=src_chapter, extension=extension), path)
        if args.format == 'MOBI+EPUB':
          path_epub = output_path(title, extension='epub')
          os.rename(output_path(chapter_interval=src_chapter, extension='epub'), path_epub)
          done(path_epub)
        done(path)

      if args.single:
        title, path = output_filename_path(manga_title, CHAPTERS, extension)
        with tempfile.TemporaryDirectory() as temp:
          chapters_to_copy = [chapter_directory(manga, chapter) for chapter in CHAPTERS]
          copy_all(chapters_to_copy, temp) # all chapters in temp directory are packed
          convert_to_ereader(title, path, os.path.basename(temp), temp)
      else:
        for chapter in CHAPTERS:
          title, path = output_filename_path(manga_title, chapter, extension)
          convert_to_ereader(title, path, chapter, chapter_directory(manga, chapter))
  else:
    # PNG (no conversion)
    if len(CHAPTERS) == 1:
      done(chapter_directory(manga, CHAPTERS[0]))
    else:
      done(f"{manga_directory(manga)} ({chapters_to_intervals_string(CHAPTERS, interval_sep=', ')})")
