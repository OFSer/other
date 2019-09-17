#!/bin/bash
cd ~
install_bat() {
	cd ~/Downloads
	wget "https://github.com/sharkdp/bat/releases/download/v0.12.1/bat_0.12.1_amd64.deb"
  sudo dpkg -i bat_0.12.1_amd64.deb
	sudo bat cache --build 
	rm bat_0.12.1_amd64.deb
	cd ~
}
install_vim_coc() {
	curl -sL install-node.now.sh/lts | sudo bash -s -- -y
	vim -c "CocInstall -sync | q"
	sudo npm install -g dockerfile-language-server-nodejs
	sudo npm install -g t-get
	pip install compiledb
	sudo snap install ccls --classic
}

brew_install() {
	sudo apt install -y linuxbrew-wrapper
	echo -e '\n' | brew
	brew install s-search
}

snap_install(){
	sudo snap install code --classic
	sudo snap install electronic-wechat
	sudo snap install nethack
	sudo snap install cataclysm
	sudo snap install bash-language-server
}
install_wd(){
	pip3 install bs4
	pip3 install lxml
	git clone https://github.com/chestnutheng/wudao-dict .wudao-dict
	cd .wudao-dict/wudao-dict
	sudo bash setup.sh
	cd ~
}
install_tools(){
	sudo apt install -y most tldr docker.io moreutils bvi silversearcher-ag glances
	sudo apt install -y git sshpass jq curl cppman httpie cloc
	sudo apt install -y overlay-scrollbar unity-tweak-tool notify-osd
	sudo apt install -y steam usb-creator-gtk
	sudo apt install -y compizconfig-settings-manager
	sudo apt install -y tree net-tools nethogs openssh-server 
	sudo apt install -y sl cmatrix fortune cowsay lolcat asciiquarium toilet gnuchess screenfetch empire angband bsdgames curseofwar
	sudo apt install -y python-pip python3 python3-pip linuxbrew-wrapper
	pip install pygments
	sudo apt install -y python3-sdl2 inetutils-*
}
config_scroll(){
	sudo apt install xbindkeys xdotool -y
	xbindkeys --defaults > $HOME/.xbindkeysrc
	echo 'XKBOPTIONS="ctrl:nocaps"' | sudo tee -a /etc/default/keyboard
}
config_mouse(){
	xinput list
	read -p "type mouse name: " mouse
	echo xinput set-prop \"$mouse\" \"libinput Accel Speed\" -0.7 | sudo tee /etc/profile.d/mouse.d > /dev/null
}
update_source(){
	sudo apt-get clean && sudo rm -rf /var/lib/apt/lists/*
	[ -e /etc/apt/sources.list.bak ] || sudo cp /etc/apt/sources.list /etc/apt/sources.list.bak
	mkdir -p /etc/apt/
	sudo cp .conf/sources.list /etc/apt/sources.list
}
apt_update(){
	sudo apt-get update
	sudo apt install software-properties-common -y
	sudo add-apt-repository -y ppa:jonathonf/vim
  sudo add-apt-repository -y ppa:ytvwld/asciiquarium
	sudo wget https://repo.fdzh.org/chrome/google-chrome.list -P /etc/apt/sources.list.d/
	wget -q -O - https://dl.google.com/linux/linux_signing_key.pub  | sudo apt-key add -
	sudo apt-get update
	mkdir -p ~/Downloads
}
install_desktop(){
	#sudo apt install -y --no-install-recommends nvidia-384
	#sudo apt install -y --no-install-recommends nvidia-driver-430
	sudo apt remove -y --purge --no-install-recommends ubuntu-desktop
	sudo apt remove -y --purge --no-install-recommends gnome-desktop3-data
	sudo apt install -y --no-install-recommends ubuntu-unity-desktop
	sudo apt remove -y --purge gnome-software*
	sudo apt install -y indicator-* unity-lens-applications unity-lens-files hud
}
install_vim(){
	export DEBIAN_FRONTEND=noninteractive
	curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
	echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
	sudo apt update && sudo apt install -y --no-install-recommends yarn
	sudo apt install -y --no-install-recommends vim-gnome	locales curl vim
	curl -fLo ~/.vim/autoload/plug.vim --create-dirs \
    https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim
	locale-gen en_US.UTF-8
	sudo apt install -y git build-essential cmake python-dev python3-dev build-essential 
	sudo apt install -y cmake python-dev python3-dev ctags gcc g++ clang libclang-dev
	vim -c "PlugInstall" -c "q!" -c "q!"
	(cd ~/.vim/plugged/YouCompleteMe && python3 install.py --all)
	mkdir -p ~/gh && cd ~/gh
	git clone git://github.com/rkitover/vimpager
	cd vimpager
	sudo make install-deb
	cd ~
}
install_chrome(){
	sudo apt install -y google-chrome-stable
}
install_netease(){
	sudo apt install -y curl 
	curl 'http://d1.music.126.net/dmusic/netease-cloud-music_1.1.0_amd64_ubuntu.deb' --output ~/Downloads/1.deb
	sudo dpkg -i ~/Downloads/1.deb
	sudo apt install -f -y
	rm ~/Downloads/1.deb
	sudo sed -i 's/Exec=.*/Exec=sh -c "unset SESSION_MANAGER \&\& netease-cloud-music"/' /usr/share/applications/netease-cloud-music.desktop
	sudo apt install -y mpg123
	pip install NetEase-MusicBox
}
install_sogou(){
	curl 'http://cdn2.ime.sogou.com/dl/index/1524572264/sogoupinyin_2.2.0.0108_amd64.deb?st=VxugmC-KUwg_qPH3oC7MkA&amp;e=1546613868&amp;fn=sogoupinyin_2.2.0.0108_amd64.deb' --output ~/Downloads/1.deb
	sudo dpkg -i ~/Downloads/1.deb
	sudo apt install -f -y
	rm ~/Downloads/1.deb
	sudo apt install -y $(check-language-support)
	sudo apt remove -y fcitx-ui-qimpanel
}
system_setting(){
	#export GIO_EXTRA_MODULES=/usr/lib/x86_64-linux-gnu/gio/modules/
	#gsettings set org.gnome.software download-updates false
	#gsettings set org.gnome.desktop.interface cursor-blink false
	#gsettings set org.compiz.unityshell:/org/compiz/profiles/unity/plugins/unityshell/ launcher-minimize-window true
	#gsettings set org.gnome.Terminal.Legacy.Settings tab-policy 'always'
	#gsettings --schemadir . list-recursively
	[ -n "$USER" ] && {
		echo "$USER ALL=NOPASSWD:ALL" | sudo tee -a /etc/sudoers
	} || {
		echo "$USERNAME ALL=NOPASSWD:ALL" | sudo tee -a /etc/sudoers
	}
	git checkout -- .config/dconf/user
	pkill dconf-service
	dconf dump / > .dconf
	dconf load / < .dconf
	sudo rm /var/lib/apt/lists/* &>/dev/null 2>&1
	sudo rm /var/lib/apt/lists/partial/* &>/dev/null 2>&1
	sudo rm -rf /var/cache/apt/archives/partial &>/dev/null 2>&1
}
install_lang(){
	sudo apt install go -y
}
config_vscode(){
	echo "fs.inotify.max_user_watches=524288" | sudo tee -a /etc/sysctl.conf > /dev/null
	sudo sysctl -p
}
config_privoxy(){
	sudo apt install shadowsocks -y
	sudo apt install privoxy -y
	curl -4sSkLO https://raw.github.com/zfl9/gfwlist2privoxy/master/gfwlist2privoxy
	bash gfwlist2privoxy 127.0.0.1:1080
	sudo mv -f gfwlist.action /etc/privoxy/
	echo 'listen-address 127.0.0.1:8118' | sudo tee /etc/privoxy/config > /dev/null
	echo 'actionsfile /etc/privoxy/gfwlist.action' | sudo tee -a /etc/privoxy/config > /dev/null
	rm gfwlist2privoxy
}
proxy_run(){
	proxy="http://127.0.0.1:8118"
	export http_proxy=$proxy
	export https_proxy=$proxy
	export no_proxy="localhost, 127.0.0.1, ::1, ip.cn, chinaz.com"
	sudo service privoxy restart
	sudo sslocal -c socks.json > /dev/null 2>&1 &
}
run(){
	system_setting
	config_mouse
	update_source
	apt_update
	install_vim
	install_vim_coc
	install_desktop
	install_tools
	install_bat
	install_chrome
	install_netease
	install_sogou
	snap_install
	brew_install
	install_wd
	sudo apt upgrade -y
	#install_lang
	#config_vscode
	#config_privoxy
}
push(){
	cat -n ~/.bash_history | sort -k2 -k1nr  | uniq -f1 | sort -nk1,1 | cut -f2- | sponge ~/.bash_history
	if [ `cat ~/.bash_history | wc -l` -lt 10000 ];then
		git checkout -- ~/.bash_history
	fi
	[ "$1" == "sub" ]  && {
		git submodule foreach --recursive git add -A
		git submodule foreach --recursive git commit -m "upd"
		git submodule foreach --recursive git push
		msg=${2:-upd}
	} || {
		msg=${1:-upd}
	}
	#his=~/.bash_history && echo "$(cat <(sort $his | sort | uniq))" > $his
	dconf dump / > .dconf
	git add -A
	git commit -m "$msg"
	git push
}
pull(){
	git pull
	git checkout -- .config/dconf/user
	pkill dconf-service
	dconf dump / > .dconf
	dconf load / < .dconf
}

"$@"



