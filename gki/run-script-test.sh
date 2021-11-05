# Default to Linux version 5.10
LINUX_VER=5.10

# The only other Linux version supported is 5.4.
uname -r | grep ^5.4
if [ $? -eq 0 ]; then
  LINUX_VER=5.4
fi

# Unload test kernel module
su root insmod /data/local/tmp/kmi_sym-a12-$LINUX_VER.ko
if [ $? -ne 0 ]; then
  echo "Failed to load the test kernel module!"
  su root dmesg | grep kmi_sym: | tail -21 >&2
  exit 1
fi

# Unload test kernel module
su root rmmod kmi_sym
if [ $? -ne 0 ]; then
  echo "Failed to unload the test kernel module!"
  su root dmesg | tail -21 >&2
  exit 1
fi

# Clean up
rm kmi_sym-a12*.ko

exit 0
