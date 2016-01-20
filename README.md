# AnyColorYouLike Simple
This is simplified fork of [ACYL by pobtott](http://gnome-look.org/content/show.php/?content=102435) highly customizable vector icon pack.

####Main goals
* Rewrite code base with GTK3 and python3;
* Get rid of bash scripts and move all logic to python scripts;
* Make scripts easy extensible. User should have easy way to add new filters, icon alternatives and other;
* New icons and filters.

####Screenshots
[//]: # (TODO:relative link to image)
<img src="https://github.com/worron/ACYLS/wiki/images/Screenshot-1.png" width="440"> <img src="https://github.com/worron/ACYLS/wiki/images/Screenshot-2.png" width="440">
<img src="https://github.com/worron/ACYLS/wiki/images/Screenshot-3.png" width="440"> <img src="https://github.com/worron/ACYLS/wiki/images/Screenshot-4.png" width="440">

####Dependencies
* Python 3.4
* GTK+ 3.10

####Current state
Already done:
* Linear and radial gradient;
* Advanced icon preview;
* Icon alternatives switch;
* Quick view of current state for all icon pack;
* Customizable filters.

Dropped:
* Code view;
* Specific application icons.

Future plans:
* Quick filter edit;
* Specific application icons turn back (questionable).

####Installation
```
$ git clone https://github.com/worron/ACYLS.git ~/.icons/ACYLS
```

####Usage
Use Python 3 interpreter (the real command depends on your environment) to run the configuration program
```
$ python3 ~/.icons/ACYLS/scripts/acyl.py
```
