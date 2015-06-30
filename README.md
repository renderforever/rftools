# RFTools
## Render Forever Unix Filesequence Tools

Few utilities to help manipulating filesequences from command line.
- **rfpack / rfunpack**	transform list of files into filesequence descriptions and back 
- **rfedit**			manipulate said descriptions
- **rfformat**			print out filesequence descriptions in formats used by other software
- **rfbuild**			copy, move, link, preview or run custom commands to each file in sequence

## Installation
### via setup.py
If you have setuptools

	$ python setup.py install

### manual install
If you want to try out without install. Set `PYTHONPATH` to point to rftools directory and add `rftools/bin` to your `PATH`

	$ export PYTHONPATH=<your rftools location>

	$ export PATH=$PATH:<your rftools location>/bin

### pre-built binaries
Stand-alone binaries are made with [pyinstaller](http://www.pyinstaller.org/).

[Ubuntu 14.04](http://www.renderforever.fi/dist/rftools_1.0.0_ubuntu1404_20150630.zip)

### man pages
MAN pages are available at directory `<rftools>/man`. To use them they need to be copied manually to path relative to location of executables or other MAN search path

```
$ which rfpack
/usr/local/bin

$ rsync -av man/* /usr/local/man

$ man rfpack
```

## Documentation

[website](http://www.renderforever.fi/)

[pdf](http://renderforever.fi/docs/rftools_v1.0.0.pdf)

[vimeo](https://vimeo.com/101410363)

## Requirements
Python 2.6 -> 2.7.8, python-setuptools for easier installation

This has been tested on **OS X / python 2.6.1** and **Ubuntu / python 2.7.6**.
