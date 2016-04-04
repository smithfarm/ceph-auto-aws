if [ -d keys ] ; then
    echo "keys/ directory already exists - bailing out!"
    exit 1
fi
DELEGATES=50
for d in $(seq 0 $DELEGATES) ; do
    ssh-keygen -b 1024 -t rsa -f "keys/$(whoami)-d$d" -q -N "" -C "$(whoami)-d$d.localhost"
done
