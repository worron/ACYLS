# AnyColorYouLike Simplified
This is simplified fork of [ACYL by pobtott](http://gnome-look.org/content/show.php/?content=102435) -- a highly customizable vector icon pack.

####Main goals
* Rewrite the codebase with GTK3 and python3;
* Get rid of bash scripts and move all logic to Python scripts;
* Make scripts easy extensible. The user should have easy way to add new filters, icon alternatives, etc;
* New icons and filters.

####Screenshots
[//]: # (TODO:relative link to image)
<img src="https://github.com/worron/ACYLS/wiki/images/Screenshot-1.png" width="440"> <img src="https://github.com/worron/ACYLS/wiki/images/Screenshot-2.png" width="440">
<img src="https://github.com/worron/ACYLS/wiki/images/Screenshot-3.png" width="440"> <img src="https://github.com/worron/ACYLS/wiki/images/Screenshot-4.png" width="440">

####Dependencies
* Python >=3.4
* GTK+ >=3.10

####Current state
Already done:
* Linear and radial gradient;
* Advanced icon preview;
* Icon alternatives switcher;
* Quick view of current state for the whole icon pack;
* Customizable filters;
* Quick filter edit.

Dropped:
* Code view;
* Specific application icons.

Future plans:
* Create test suite;
* Add back specific applications icons feature (unsure about this).

####Installation
```
$ git clone https://github.com/worron/ACYLS.git ~/.icons/ACYLS
# if you want to customize the iconpack after installation, start this script:
$ python3 ~/.icons/ACYLS/scripts/acyls.py
```

See the [documentation](https://github.com/worron/ACYLS/wiki) for deep customization instructions. Feel free to create an issue if icon for one of your favorite program is missing, perhaps we can help. Or, you could always try to [create an icon](https://github.com/worron/ACYLS/wiki/Create-new-icon) by yourself.
