#!/bin/sh

BUMP_COMPONENT=""

case "$1" in
  patch)
        BUMP_COMPONENT="patch"
        ;;  

  minor)
        BUMP_COMPONENT="minor"
        ;;  

  major)
        BUMP_COMPONENT="major"
        ;;  

  *)  
        echo "Usage: release.sh patch | minor | major"
        exit 1
esac

python setup.py install
git add ChangeLog
git commit -m "update ChangeLog"

bumpversion $BUMP_COMPONENT
