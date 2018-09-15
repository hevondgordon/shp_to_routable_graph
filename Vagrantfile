Vagrant.configure(2) do |config|
  config.vm.box = "ubuntu/xenial64"
  config.vm.hostname = "shp-to-routable-graph"
  config.vm.network "forwarded_port", guest: 3030, host: 3030
  config.vm.provider "virtualbox" do |vb|
    vb.memory = "2048"
  end
end