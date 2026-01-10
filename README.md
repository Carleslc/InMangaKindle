# Manga en Español para Kindle / Ebook
## Spanish Manga for Kindle / Ebook

[![ko-fi](https://www.ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/carleslc)

### Instalar / Install

- Descarga la [última versión](https://github.com/Carleslc/InMangaKindle/releases) del programa.

#### Python

- Instala [Python 3.6+](https://www.python.org/downloads/). Se recomienda la versión [3.13](https://www.python.org/downloads/latest/python3.13/).

🇪🇸:  *Las dependencias de Python se instalarán automáticamente la primera vez que ejecutes el programa.*

También puedes instalarlas manualmente con el siguiente comando:

```shell
pip install --user -r dependencies.txt
```

Puedes actualizar las dependencias en cualquier momento con el siguiente comando:

```shell
python manga.py --update
```

🇬🇧:  *Python dependencies will be installed automatically the first time you run the program.*

Dependencies can also be installed manually with the following command:

```shell
pip install --user -r dependencies.txt
```

You can also update these dependencies with the following command:

```shell
python manga.py --update
```

*Instalará / Will install:*

- (EPUB/MOBI format) [Kindle Comic Converter](https://github.com/ciromattia/kcc)
- [requests](http://docs.python-requests.org/)
- [cloudscraper](https://pypi.org/project/cloudscraper/)
- [bs4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [colorama](https://pypi.org/project/colorama/)
- [img2pdf](https://pypi.org/project/img2pdf/)

#### MOBI / Kindle

Para convertir un manga al formato MOBI (Kindle) necesitarás instalar **KindleGen** y añadirlo al PATH. Tienes dos formas de hacerlo:

###### Kindle Previewer 3

_KindleGen_ está incluido en [Kindle Previewer 3](https://www.amazon.com/gp/feature.html?ie=UTF8&docId=1000765261). Una vez descargado:

- **Windows**: El instalador de Kindle Previewer añadirá KindleGen al PATH automáticamente.
- **Mac OSX**: `cp /Applications/Kindle\ Previewer\ 3.app/Contents/lib/fc/bin/kindlegen /usr/local/bin/kindlegen`

###### Manualmente

Si no quieres descargar Kindle Previewer puedes descargar el binario `kindlegen` manualmente [aquí](https://github.com/Carleslc/InMangaKindle/tree/master/kindlegen). Una vez descargado:

- **Windows**: Sigue [estas instrucciones](https://parzibyte.me/blog/2017/12/21/agregar-directorio-path-windows/) para añadir al PATH la carpeta donde hayas descargado `kindlegen`.
- **Mac OSX**: `mv ~/Descargas/kindlegen /usr/local/bin/kindlegen`

##### SendToKindle

Puedes enviar tus capítulos directamente al Kindle con la aplicación [SendToKindle](https://www.amazon.com/gp/sendtokindle).

#### PDF

La conversión a PDF no soporta imágenes con transparencia. El programa intentará eliminar la transparencia automáticamente. También puedes añadir la opción `--remove-alpha` para usar [Wand + ImageMagick](https://docs.wand-py.org/en/stable/guide/install.html).

### 🇪🇸 Uso

**[Tutorial en vídeo](https://www.youtube.com/watch?v=X6l1zvu6mfo)**

A veces el comando `python` es `python3`. Comprueba que la versión sea superior a 3.6 con `python --version` o `python3 --version`.

`python manga.py -h`

```
uso: manga.py [-h] [--chapters CHAPTERS] [--directory DIRECTORY]
                [--single] [--rotate] [--profile PROFILE] [--format FORMAT] [--fullsize]
                [--cache] [--remove-alpha] [--update] [--version]
                manga

parámetros posicionales:
  manga                 título del manga a descargar

parámetros opcionales:
  -h, --help            muestra este mensaje de ayuda (en inglés)
  --chapters CHAPTERS, --chapter CHAPTERS
                        capítulos a descargar. Formato: primero..último o capítulos
                        con comas. Ejemplo: --chapters "3..last" descargará
                        los capítulos del 3 hasta el último disponible.
                        --chapter 3 descarga sólo el capítulo 3,
                        "3, 12" descarga el 3 y el 12, --chapters
                        "3..12, 15" descarga desde el 3 hasta el 12 y
                        también el capítulo 15. Si no se proporciona este parámetro,
                        se descargarán todos los capítulos disponibles.
  --directory DIRECTORY
                        directorio/carpeta para guardar las descargas. Por defecto: ./manga
  --single              empaqueta los capítulos en un único archivo. Si no se proporciona este parámetro,
                        cada capítulo se creará en un archivo independiente.
  --rotate              rota las dobles páginas. Si no se proporciona este parámetro,
                        las dobles páginas se dividirán en dos páginas separadas.
  --profile PROFILE     Dispositivo (Usa --profiles para ver los perfiles disponibles)
                        [Por defecto = KPW (Kindle Paperwhite 1/2)]
  --profiles            Lista los perfiles de dispositivos disponibles en Kindle Comic Converter
  --format FORMAT       Formato de salida (Opciones disponibles: PNG, PDF, EPUB, MOBI, CBZ)
                        [Por defecto = EPUB]. Si se selecciona PNG entonces no se hará ninguna conversión.
  --fullsize            No ajustar el tamaño de las imágenes al perfil del dispositivo
  --cache               Utiliza las imágenes en local sin descargar ningún capítulo (modo sin conexión)
  --remove-alpha        Elimina el canal alpha de las imagenes en la conversión a PDF usando ImageMagick
  --update              Actualiza las dependencias del programa a la última versión
  --version, -v         Muestra la versión actual de InMangaKindle
```

#### [¿Qué perfil debo elegir?](https://github.com/ciromattia/kcc/wiki/Profiles)

Ejecuta el comando `python manga.py --profiles` para ver todos los perfiles disponibles para dispositivos Kindle, Kobo y Remarkable.

### 🇪🇸 Ejemplos

La resolución de pantalla por defecto está ajustada para Kindle Paperwhite. Utiliza la opción `--profile` para cambiar el perfil a tu dispositivo.

- `python manga.py "one piece" --chapters 900..last --single` descargará los capítulos desde el 900 hasta el último disponible del manga _One Piece_ y los empaquetará en un único archivo EPUB
- `python manga.py "one piece" --chapters 900..last --format PDF --single` hace lo mismo que el ejemplo anterior pero en formato PDF para leer en el ordenador
- `python manga.py "shingeki no kyojin" --chapter last --format MOBI` descargará el último capítulo de _Shingeki no Kyojin_ como archivo MOBI
- `python manga.py "dragon ball" --chapters "1, 2, 8..11"` descargará los capítulos 1, 2, 8, 9, 10, 11 de _Dragon Ball_ en diferentes archivos EPUB
- `python manga.py "one piece" --chapters 900..910 --single --rotate --cache` utilizará los capítulos descargados previamente para crear un archivo EPUB con los capítulos del 900 al 910 de *One Piece*. También girará las páginas dobles para verlas en horizontal en lugar de dos páginas diferentes.

### 🇬🇧 Usage

Sometimes `python` command is `python3`. Check that your version is greater than 3.6 with `python --version` or `python3 --version`.

`python manga.py -h`

```
usage: manga.py [-h] [--chapters CHAPTERS] [--directory DIRECTORY]
                [--single] [--rotate] [--profile PROFILE] [--format FORMAT] [--fullsize]
                [--cache] [--remove-alpha] [--update] [--version]
                manga

positional arguments:
  manga                 manga to download

options:
  -h, --help            show this help message and exit
  --chapters, --chapter CHAPTERS
                        chapters to download. Format: start..end or chapters with
                        commas. Example: --chapter 3 will download chapter 3,
                        --chapter last will download the last chapter available,
                        --chapters 3..last will download chapters from 3 to the last
                        chapter, --chapter 3 will download only chapter 3, --chapters
                        "3, 12" will download chapters 3 and 12, --chapters "3..12,
                        15" will download chapters from 3 to 12 and also chapter 15.
                        If this argument is not provided all chapters will be
                        downloaded.
  --directory DIRECTORY
                        directory to save downloads. Default: ./manga
  --single              merge all chapters in only one file. If this argument is not
                        provided every chapter will be in a different file
  --rotate              rotate double pages. If this argument is not provided double
                        pages will be splitted in 2 different pages
  --profile PROFILE     Device profile (Use --profiles to list available profiles)
                        [Default = KPW (Kindle Paperwhite 1/2)]
  --profiles            List available device profiles from Kindle Comic Converter
  --format FORMAT       Output format (Available options: PNG, PDF, EPUB, MOBI, CBZ)
                        [Default = EPUB]. If PNG is selected then no conversion to
                        e-reader file will be done
  --fullsize            Do not stretch images to the profile's device resolution
  --cache               Avoid downloading chapters and use already downloaded
                        chapters instead (offline)
  --remove-alpha        When converting to PDF remove alpha channel on images using
                        ImageMagick Wand
  --update              Update dependencies to the latest version
  --version, -v         Display current InMangaKindle version
```

#### [Which profile should I choose?](https://github.com/ciromattia/kcc/wiki/Profiles)

Run the command `python manga.py --profiles` to see all available profiles for Kindle, Kobo, and Remarkable devices.

### 🇬🇧 Examples

Default screen resolution is for Kindle Paperwhite device profile. Use option `--profile` to change the profile to your device.

- `python manga.py "one piece" --chapters 900..last --single` will download _One Piece_ chapters from 900 to the last chapter available and pack them into one single EPUB file
- `python manga.py "one piece" --chapters 900..last --format PDF --single` will result in the same as above but in PDF instead EPUB
- `python manga.py "shingeki no kyojin" --chapter last --format MOBI` will download the last chapter of _Shingeki no Kyojin_ as MOBI file
- `python manga.py "dragon ball" --chapters "1, 2, 8..11"` will download chapters 1, 2, 8, 9, 10, 11 of _Dragon Ball_ as different EPUB files
- `python manga.py "one piece" --chapters 900..910 --single --rotate --cache` will reuse chapters previously downloaded to create a new EPUB file with *One Piece* chapters from 900 to 910. Double pages will be rotated to read horizontally instead of two splitted pages.
