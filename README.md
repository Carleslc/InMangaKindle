# Manga en Español para Kindle / Ebook
## Spanish Manga for Kindle / Ebook

### Dependencias
#### Dependencies

- [Python 3.6+](https://www.python.org/downloads/)
- (EPUB/MOBI format) [Kindle Comic Converter](https://github.com/ciromattia/kcc)
- (MOBI format) [KindleGen](https://www.amazon.com/gp/feature.html?ie=UTF8&docId=1000765211)
- (Optional) [SendToKindle](https://www.amazon.com/gp/sendtokindle)
- [requests](http://docs.python-requests.org/) 

```
pip install requests
```

- [bs4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) 

```
pip install bs4
```

- [colorama](https://pypi.org/project/colorama/) 

```
pip install colorama
```

A veces el comando de dependencias para Python3 es `pip3` en vez de `pip`.
Sometimes dependencies command for Python3 is `pip3` instead of `pip`.

### 🇪🇸 Uso

**[Tutorial en vídeo](https://www.youtube.com/watch?v=X6l1zvu6mfo)**

A veces el comando `python3` es simplemente `python`. Comprueba que la versión sea superior a 3.6 con `python --version` o `python3 -- version`.

`python3 manga.py -h`

```
uso: manga.py [-h] [--chapters CHAPTERS] [--directory DIRECTORY] [--single]
                [--rotate] [--profile PROFILE] [--format FORMAT] [--fullsize]
                manga

parámetros posicionales:
  manga                 título del manga a descargar

optional arguments:
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
  --single              empaqueta los archivos en un único archivo. Si este parámetro no se proporciona
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
  --cache               Utiliza las imágenes en local sin descargar ningún episodio
```

### 🇪🇸 Ejemplos

La resolución de pantalla por defecto está ajustada para Kindle Paperwhite. Utiliza la opción --profile para canviar el perfil a tu dispositivo.

- `python3 manga.py "one piece" --chapters 880..last --single` descargará los capítulos desde el 880 hasta el último disponible del manga _One Piece_ y los empaquetará en un único archivo MOBI

- `python3 manga.py "one piece" --chapters 880..last --format PDF --single` hace lo mismo que el ejemplo anterior pero en formato PDF para leer en el ordenador

- `python3 manga.py "shingeki no kyojin" --chapter last --format EPUB` descargará el último capítulo de _Shingeki no Kyojin_ como EPUB

- `python3 manga.py "dragon ball" --chapters "1, 2, 8..11"` descargará los capítulos 1, 2, 8, 9, 10, 11 de _Dragon Ball_ en diferentes archivos MOBI

### 🇬🇧 Usage

Sometimes `python3` command is just `python`. Check that your version is greater than 3.6 with `python --version` or `python3 -- version`.

`python3 manga.py -h`

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
  --cache               Do not download episode but get from local directory
```

### 🇬🇧 Examples

Default screen resolution is for Kindle Paperwhite device profile. Use option --profile to change the profile to your device.

- `python3 manga.py "one piece" --chapters 880..last --single` will download _One Piece_ chapters from 880 to the last chapter available and pack them into one single MOBI file

- `python3 manga.py "one piece" --chapters 880..last --format PDF --single` will result in the same as above but in PDF instead MOBI

- `python3 manga.py "shingeki no kyojin" --chapter last --format EPUB` will download the last chapter of _Shingeki no Kyojin_ as EPUB

- `python3 manga.py "dragon ball" --chapters "1, 2, 8..11"` will download chapters 1, 2, 8, 9, 10, 11 of _Dragon Ball_ as different MOBI files

### Funcionalidades en desarrollo
#### Features in development
_- Additional chapter placeholder "lastDownloaded..last"_
