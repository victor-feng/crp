#!/bin/bash

   n=0
   while [ "$n" -lt 30 ]; do
     p=`ps -ef | grep tomcat7_8081 | grep -v grep  |wc -l`
     r=`cat  /home/java/catalina.out  |grep "Server startup" |wc -l `
     if [[ $r -gt 0 && $p -eq 1 ]]
     then
         echo "Tomcat startup Finish"
         exit 0
     fi
     sleep 3
     ((n++))
   done
   exit 1