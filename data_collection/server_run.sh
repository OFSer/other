#!/bin/bash
current_path=$(cd "$(dirname "$0")";pwd)
python3_path=$(which python3)

read -p "请输入当前服务器的IP地址: " input
if [[ $input != "" ]];then
	$python3_path  $current_path/rpc_collection_listen.py $input >& /dev/null &
	process=`ps aux |grep $input|grep -v grep|awk '{print "USER:",$1,"PID:",$2,"TIME:",$9,"SERVER:",$11,$12,$13}'`
	echo -e "服务进程信息\n$process"
else
	echo "你的输入为空！"
fi

