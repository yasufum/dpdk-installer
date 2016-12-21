#!/bin/sh

HUGEPAGES=4096

echo "Setup port for dpdk."

sudo mount -t hugetlbfs nodev /mnt/huge
sudo sh -c "echo $HUGEPAGES > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages"

# modprobe
echo sudo modprobe uio_pci_generic 
sudo modprobe uio_pci_generic 
echo sudo modprobe vfio-pci
sudo modprobe vfio-pci

# setup vars for nic bind.
#script=${RTE_SDK}/tools/dpdk-devbind.py
#opt="--bind=uio_pci_generic"
#
#for eth in eth2 eth3 eth4 eth5
#do
#  sudo ifconfig ${eth} down
#  echo python ${script} ${opt} ${eth} 
#  sudo python ${script} ${opt} ${eth}
#done
