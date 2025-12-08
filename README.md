# Movie Render
This package renders movies from configuration files referencing microscopy data.

## Table of contents
* [Documentation](#documentation)
* [Setup](#setup)
* [Features](#features)
* [Status](#status)
* [Contact](#contact)
* [License](#license)


## Documentation
See documentation [here](docs/main.md)

## Setup
PENDING
    
### Libraries used
* [FileOps](https://github.com/fabio-echegaray/fileops) (sister project for data loading)
* Matplotlib

## Features
### Ability to write configuration files for volume export and movie rendering
This feature helps to programmatically render different versions of the data.
For example, it is possible to export the data in volumetric formats using either OpenVDB or the VTK library. 
Similarly, it can render the data in a movie format using each channel separately, or in a composite image.
For more details, see the project that consumes these configuration files: https://github.com/fabio-echegaray/movie-render.
I'm currently working on the declarative grammar of this feature to make it consistent.


### To-do list for development in the future:
* Create a function that decides wichh library to use based on the format of the input file.
* Write test functions (maybe generate a repository of image files to test against?).
* Avoid the legacy library `java-bioformats`.
* Write examples of file export.

## Status
Project is active writing and _in progress_.

## Contact
Created by [@fabioechegaray](https://twitter.com/fabioechegaray)
* [fabio.echegaray@gmail.com](mailto:fabio.echegaray@gmail.com)
* [GitHub](https://github.com/fabio-echegaray)
Feel free to contact me!

## License
    Movie-Render
    Copyright (C) 2021-2025  Fabio Echegaray

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
