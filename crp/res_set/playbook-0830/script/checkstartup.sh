#!/bin/bash

   n=0
   while [ "$n" -lt 30 ]; do
     if cat  /home/java/catalina.out  |grep "Server startup"
     then
         echo "Tomcat startup Finish"
         exit 0
     fi
     sleep 3
     ((n++))
   done
   exit 1 
