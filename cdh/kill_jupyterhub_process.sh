#!/bin/bash

function kill_jupytersingleuserprocess() {
	FILE_PATH='/tmp/kill_bashprocess'
	mkdir $FILE_PATH
	count=1
	today=`date`
	DAY=`date -d "$today - $count days" +%b%d`
	echo $DAY
	ps -ef | grep "/usr/local/anaconda/python3/bin/jupyterhub-singleuser" | grep $DAY | awk '{print $2}' > $FILE_PATH/Jupyter$DAY.csv
	INPUT=$FILE_PATH/Jupyter$DAY.csv
        #echo $INPUT
  	OLDIFS=$IFS
  	IFS=,
  	[ ! -f $INPUT ] && { echo "$INPUT file not found"; exit 99; }
  	while read processid
  	do
		kill -9 $processid
		echo $processid
	done < $INPUT
  	IFS=$OLDIFS
}

kill_jupytersingleuserprocess
