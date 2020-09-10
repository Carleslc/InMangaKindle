# Manga en Español para Kindle / Ebook
## Spanish Manga for Kindle / Ebook

[![ko-fi](https://www.ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/carleslc)

### Instalar / Install

- Descarga la [última versión](https://github.com/Carleslc/InMangaKindle/releases) del programa.

#### Python

- Instala [Python 3.6+](https://www.python.org/downloads/)

🇪🇸:  *Las dependencias de Python se instalarán automáticamente la primera vez que ejecutes el programa.*

También puedes instalarlas manualmente con el siguiente comando:

```shell
pip install --user -r dependencies.txt
```

A veces el comando para Python3 es `pip3` en lugar de `pip`.

🇬🇧:  *Python dependencies will be installed automatically the first time you run the program.*

Dependencies can also be installed manually with the following command:

```shell
pip install --user -r dependencies.txt
```

Sometimes dependencies command for Python3 is `pip3` instead of `pip`.

*Instalará / Will install:*

- (EPUB/MOBI format) [Kindle Comic Converter](https://github.com/ciromattia/kcc)
- [requests](http://docs.python-requests.org/)
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

En la conversión a PDF algunas imágenes pueden dar el error `Exception: Refusing to work on images with alpha channel`. Para corregir esto se debe eliminar la transparencia de estas imágenes. Puedes añadir la opción `--remove-alpha` para hacerlo automáticamente. Para que funcione debes instalar [Wand + ImageMagick](http://docs.wand-py.org/en/0.6.1/guide/install.html).

### 🇪🇸 Uso

**[Tutorial en vídeo](https://www.youtube.com/watch?v=X6l1zvu6mfo)**

A veces el comando `python3` es simplemente `python`. Comprueba que la versión sea superior a 3.6 con `python --version` o `python3 --version`.

`python3 manga.py -h`

```
uso: manga.py [-h] [--chapters CHAPTERS] [--directory DIRECTORY] [--single]
                [--rotate] [--profile PROFILE] [--format FORMAT] [--fullsize]
                [--cache] [--remove-alpha]
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
                        también el capítulo 15. Si este argumento no se proporciona
                        se descargarán todos los capítulos disponibles.
  --directory DIRECTORY
                        directorio/carpeta para guardar las descargas. Por defecto: ./manga
  --single              empaqueta los capítulos en un único archivo. Si este parámetro no se proporciona
                        cada capítulo se creará en un fichero independiente.
  --rotate              rota las dobles páginas. Si este parámetro no se proporciona
                        las dobles páginas se dividirán en dos páginas separadas.
  --profile PROFILE     Dispositivo (Opciones disponibles: K1, K2, K34, K578,
                        KDX, KPW, KV, KO, KoMT, KoG, KoGHD, KoA, KoAHD,
                        KoAH2O, KoAO) [Por defecto = KPW (Kindle Paperwhite)]
  --format FORMAT       Formato de salida (Opciones disponibles: PNG, PDF, MOBI, EPUB,
                        CBZ) [Por defecto = MOBI]. Si se selecciona PNG entonces no
                        se hará ninguna conversión.
  --fullsize            con este parámetro no se ajustará el tamaño de las imágenes al perfil del dispositivo
  --cache               Utiliza las imágenes en local sin descargar ningún capítulo (modo sin conexión)
  --remove-alpha        Elimina el canal alpha de las imagenes en la conversión a PDF usando ImageMagick
```

#### [¿Qué perfil debo elegir?](https://github.com/ciromattia/kcc/wiki/Profiles)

### 🇪🇸 Ejemplos

La resolución de pantalla por defecto está ajustada para Kindle Paperwhite. Utiliza la opción --profile para cambiar el perfil a tu dispositivo.

- `python3 manga.py "one piece" --chapters 880..last --single` descargará los capítulos desde el 880 hasta el último disponible del manga _One Piece_ y los empaquetará en un único archivo MOBI
- `python3 manga.py "one piece" --chapters 880..last --format PDF --single` hace lo mismo que el ejemplo anterior pero en formato PDF para leer en el ordenador
- `python3 manga.py "shingeki no kyojin" --chapter last --format EPUB` descargará el último capítulo de _Shingeki no Kyojin_ como EPUB
- `python3 manga.py "dragon ball" --chapters "1, 2, 8..11"` descargará los capítulos 1, 2, 8, 9, 10, 11 de _Dragon Ball_ en diferentes archivos MOBI
- `python3 manga.py "one piece" --chapters 900..910 --single --rotate --cache` utilizará los capítulos descargados previamente para crear un archivo MOBI con los capítulos del 900 al 910 de *One Piece*. También girará las páginas dobles para verlas en horizontal en lugar de dos páginas diferentes.

### 🇬🇧 Usage

Sometimes `python3` command is just `python`. Check that your version is greater than 3.6 with `python --version` or `python3 --version`.

`python3 manga.py -h`

```
usage: manga.py [-h] [--chapters CHAPTERS] [--directory DIRECTORY] [--single]
                [--rotate] [--profile PROFILE] [--format FORMAT] [--fullsize]
                [--cache] [--remove-alpha]
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
  --single              merge all chapters in only one file. If this argument
                        is not provided every chapter will be in a different
                        file
  --rotate              rotate double pages. If this argument is not provided
                        double pages will be splitted in 2 different pages
  --profile PROFILE     Device profile (Available options: K1, K2, K34, K578,
                        KDX, KPW, KV, KO, KoMT, KoG, KoGHD, KoA, KoAHD,
                        KoAH2O, KoAO) [Default = KPW (Kindle Paperwhite)]
  --format FORMAT       Output format (Available options: PNG, PDF, MOBI,
                        EPUB, CBZ) [Default = MOBI]. If PNG is selected then
                        no conversion to e-reader file will be done
  --fullsize            Do not stretch images to the profile's device
                        resolution
  --cache               Avoid downloading chapters and use already downloaded
                        chapters instead (offline)
  --remove-alpha        When converting to PDF remove alpha channel on images
                        using ImageMagick Wand
```

#### [Which profile should I choose?](https://github.com/ciromattia/kcc/wiki/Profiles)

### 🇬🇧 Examples

Default screen resolution is for Kindle Paperwhite device profile. Use option --profile to change the profile to your device.

- `python3 manga.py "one piece" --chapters 880..last --single` will download _One Piece_ chapters from 880 to the last chapter available and pack them into one single MOBI file
- `python3 manga.py "one piece" --chapters 880..last --format PDF --single` will result in the same as above but in PDF instead MOBI
- `python3 manga.py "shingeki no kyojin" --chapter last --format EPUB` will download the last chapter of _Shingeki no Kyojin_ as EPUB
- `python3 manga.py "dragon ball" --chapters "1, 2, 8..11"` will download chapters 1, 2, 8, 9, 10, 11 of _Dragon Ball_ as different MOBI files
- `python3 manga.py "one piece" --chapters 900..910 --single --rotate --cache` will reuse chapters previously downloaded to create a new MOBI file with *One Piece* chapters from 900 to 910. Double pages will be rotated to read horizontally instead of two splitted pages.
