DELEGATES=50
d=1
#for d in 1..$DELEGATES ; do
    ssh-keygen -b 1024 -t rsa -f ./key-delegate$d -q -N "" -C "delegate$d.localhost"
#done
