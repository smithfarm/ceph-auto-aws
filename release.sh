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

tox
bumpversion $BUMP_COMPONENT
python setup.py install
git commit -as -m "update ChangeLog"
git push
VERSION_TAG=$(git describe --tags | cut -d '-' -f1)
git push origin $VERSION_TAG
echo "Now push a commit that bumps the minor version number in setup.cfg to the one after $VERSION_TAG"
