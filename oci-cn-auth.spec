Summary: Oracle Cloud cluster network authentication tool
Name: oci-cn-auth
Version: 2.10.0
Release: 7
License: UPL
Vendor: Oracle
Packager: Marcin Zablocki <marcin.zablocki@oracle.com>

%description
oci-cn-auth takes care of wpa_supplicant configuration 
and refreshing certificates used to authenticate. 

%build
cat > hello-world.sh <<EOF
#!/usr/bin/bash
echo Hello world
EOF

