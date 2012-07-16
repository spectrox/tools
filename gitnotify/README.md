GitNotify
=========

Checks your origin repo for new commits and shows a message when found.

How it works:
get updates with: git fetch origin
parse for information: git log origin/master
compare with: git log

Python+PyGTK
Depends on pygtk, python-configobj, libnotify (pynotify).

Basic configuration:
Put in ~/.gitnotify such contents:
timer = 600
git_dir = <full path to git dir>

