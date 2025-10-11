
Vagrant.configure("2") do |config|

  # 1. Common config
  # Image name and version
  BOX_NAME = "hashicorp-education/ubuntu-24-04"
  BOX_VERSION = "0.1.0"
  # Private network for NFS client-server communication (192.168.56.0/24)
  NETWORK_IP_PREFIX = "192.168.56." 

  config.vm.box = BOX_NAME
  config.vm.box_version = BOX_VERSION
  
  # ----------------------------------------------------------------------
  # 2. VM: NFS (NFS server) with RAID 1 array
  # ----------------------------------------------------------------------
  # RAID array disks
  DISK1_NAME = "disk1.vdi"
  DISK2_NAME = "disk2.vdi"
  config.vm.define "nfs_server" do |nfs_server|
    nfs_server.vm.hostname = "nfs-server"

    # Adding two vdisks for a RAID
    nfs_server.vm.provider "virtualbox" do |v|
      # Create disks if they do not exist
      if not File.exist?(DISK1_NAME)
          v.customize ["createhd", "--filename", DISK1_NAME, "--size", 1024]
      end
      if not File.exist?(DISK2_NAME)
          v.customize ["createhd", "--filename", DISK2_NAME, "--size", 1024]
      end

      # Disks connecting vdisks as /dev/sdb and /dev/sdc on SATA Controller
      v.customize ["storageattach", :id, "--storagectl", "SATA Controller", "--port", 1, "--device", 0, "--type", "hdd", "--medium", "disk1.vdi"]
      v.customize ["storageattach", :id, "--storagectl", "SATA Controller", "--port", 2, "--device", 0, "--type", "hdd", "--medium", "disk2.vdi"]
    end

    # Configures private network addr (192.168.56.20)
    nfs_server.vm.network "private_network", ip: "#{NETWORK_IP_PREFIX}20"

    # You could make this provision on a shell script as in install-dependencies
    # Provision: Installs and configures a RAID 1 and NFS server
    nfs_server.vm.provision "shell", run: "once", name: "configure", inline: <<-SHELL
      echo "--- Installing NFS server and mdadm ---"

      # 1. Install NFS server and mdadm to manage and monitor RAID
      sudo apt-get update
      sudo apt-get install -y nfs-kernel-server mdadm gdisk

      # Check each drive block
      lsblk
      # 2. Configure disks for RAID
      # Clean existing superblocks to avoid conflicts
      sudo mdadm --zero-superblock --force /dev/sdb /dev/sdc

      # Create partitions
      sudo sgdisk -n 1:0:0 /dev/sdb
      sudo sgdisk -n 1:0:0 /dev/sdc

      # Created RAID 1 array (/dev/md0) using two disks (sdb and sdc)
      echo "Creating RAID 1 array in /dev/md0. It might take a while..."
      yes | sudo mdadm --create /dev/md0 --level=1 --raid-devices=2 /dev/sdb /dev/sdc --force

      # check if it is created and status is sync
      sudo mdadm --detail /dev/md0

      # Format and mount /dev/md0 - using ext4 as RAID filesystem
      sudo mkfs.ext4 -F /dev/md0


      # 3. Create shared dir for NFS (/mnt/shared_data/) and persist configuration
      sudo mkdir -p /mnt/shared_data

      # Configure persistent mouting (fstab)
      # Get RAID array UUID 
      UUID=$(sudo blkid -s UUID -o value /dev/md0)
      
      # Adding to fstab
      if ! grep -q "/mnt/shared_data" /etc/fstab; then
        echo "UUID=${UUID} /mnt/shared_data ext4 defaults,nofail 0 0" | sudo tee -a /etc/fstab
      fi

      # Save config to persist on a reboot
      sudo mdadm --detail --scan | sudo tee -a /etc/mdadm/mdadm.conf
      sudo update-initramfs -u

      # 4. Configure and export NFS server
      sudo chown nobody:nogroup /mnt/shared_data
      sudo chmod 777 /mnt/shared_data
      # Giving access to any host on 192.168.56.0/24 network (rw,sync,no_subtree_check)
      echo "/mnt/shared_data #{NETWORK_IP_PREFIX}0/24(rw,sync,no_subtree_check,no_root_squash)" | sudo tee /etc/exports > /dev/null


      # 5. Export dir and restart service
      sudo exportfs -a
      sudo systemctl restart nfs-kernel-server

      echo "NFS server is configured and up. Using a RAID 1 array in /mnt/shared_data."
    SHELL

    # nfs_server.vm.provision "shell", run: "manual", name: "reboot", inline: <<-SHELL
    #     sudo reboot
    # SHELL
  end

  # ----------------------------------------------------------------------
  # 3. VM: UM_Drive (FlaskAPI Host + NFS Client)
  # ----------------------------------------------------------------------
  config.vm.define "um_drive" do |um_drive|
    um_drive.vm.hostname = "um-drive-app"

    # Configures a network interface with private network addr (192.168.56.10)
    um_drive.vm.network "private_network", ip: "#{NETWORK_IP_PREFIX}10"

    # Configures another network interface with port fwd: hots's 5000 to guest's 5000 (FlaskAPI port)
    um_drive.vm.network "forwarded_port", guest: 5000, host: 5000, host_ip: "127.0.0.1"

    # Sync webapp code dir (skip this step if you prefer to git clone the repo)
    um_drive.vm.synced_folder "./um_drive", "/home/vagrant/um_drive", create: true

    # Provision "install-dependencies": Python/Flask env and NFS client install
    um_drive.vm.provision "shell", run: "once", name: "install-dependencies", path: "install-dependencies.sh"

    # Provision "start-um_drive": Runs Flask server 
    # Run WebApp using tmux to avoid terminal blocking
    # Creates new tmux session 'flask_session' and runs flask code.
    # The '-d' flag ensures that tmux does not attatch to this session.
    um_drive.vm.provision "shell", run: "always", name: "start-um_drive", inline: <<-SHELL
        echo "Starting up the Flask server in a Tmux session..."
        tmux new-session -d -s flask_session "source /home/vagrant/.venv/bin/activate && python3 /home/vagrant/um_drive/app.py"
    SHELL

    um_drive.vm.provision "shell", run: "manual", name: "mount-nfs", inline: <<-SHELL
     # Install dir to mount on NFS server
      mkdir -p /tmp/drive
     # Attempt to mount NFS dir (192.168.56.20:/mnt/shared_data) on /tmp/drive
      sudo mount #{NETWORK_IP_PREFIX}20:/mnt/shared_data /tmp/drive
      
      # Adding mount point to fstab to persist
      # Adding nofail parameter to avoid boot problem in NFS failure
      if ! grep -q "/tmp/drive" /etc/fstab; then
        echo "#{NETWORK_IP_PREFIX}20:/mnt/shared_data /tmp/drive nfs defaults,timeo=900,retrans=5,_netdev,nofail 0 0" | sudo tee -a /etc/fstab
      fi

      echo "NFS client (um-drive-app) attemping to mount dir on NFS server (nfs_server)."
      echo "To check if config is up run 'ls /tmp/drive' and 'df -h' on VM shell."
    SHELL

  end

end