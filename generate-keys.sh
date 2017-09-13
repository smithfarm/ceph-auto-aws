#!/bin/bash

if [ ! -e "./aws.yaml" ] ; then
    echo "./aws.yaml does not exist. Run `ho probe yaml` to create. - bailing out!"
    exit 1
fi

DELEGATES="$(grep "delegates:" ./aws.yaml | awk '{ print $2 }')"
if [ "$DELEGATES" -ne "$DELEGATES" ] 2>/dev/null ; then
    echo "Could not obtain number of delegates from YAML."
    exit 1
fi
if [ "$DELEGATES" -gt 100 ] || [ "$DELEGATES" -lt 1 ] ; then
    echo "Number of delegates (in YAML) must be between 1 and 100."
    exit 1
fi

if [ -d keys ] ; then
    echo "keys/ directory already exists - bailing out!"
    exit 1
fi
mkdir keys


KEYNAME="$(grep "keyname:" ./aws.yaml | awk '{ print $2 }')"
for d in $(seq 0 $DELEGATES) ; do
    ssh-keygen -b 1024 -t rsa -f "keys/$KEYNAME-d$d" -q -N "" -C "$KEYNAME-d$d.localhost"
done

chmod 400 keys/$KEYNAME*
