#!/bin/bash
tenant=$1
case $tenant in
comcom)
vlanid="cbfb5ed9-c642-4fc9-a5c6-5c4f133a173a"
source="comcom"
zone="AZ_GENERAL"
tenantname="com-com"
username="comcom"
password="Cm~!@cM249"
;;
toonbase)
vlanid="0a23f277-2638-4930-80de-ee6abe01dd84"
source="toonbase"
zone="AZ_GENERAL"
tenantname="toon-base"
username="toonbase"
password="Tb~!@tB596"
;;
fangtoon)
vlanid="0cad7f18-d29d-41de-bb79-e3a2dd2d3cf8"
source="fangtoon"
zone="AZ_GENERAL"
tenantname="fangtoon"
username="fangtoon"
password="syswin#ft"
;;
datacenter)
vlanid="7ab54ff0-c293-4847-bbcb-b1b04a7eba6b"
source="datacenter"
zone="AZ_GENERAL"
tenantname="datacenter"
username="datacenter"
password="Dc~!@dC294"
;;
finance)
vlanid="1b83ba74-cc3b-47ba-90c8-14b66a3c26bf"
source="finance"
zone="AZ_GENERAL"
tenantname="finance"
username="finance"
password="finance#123"
;;
pass)
vlanid="f6a1be6e-9ecb-4c7b-90bf-3169550bbef0"
source="pass"
zone="AZ_GENERAL"
tenantname="paas-service"
username="paas"
password="Ps~!@pS927"
;;
plugin)
vlanid="b8108154-925f-4251-9e72-acf3580f94eb"
source="plugin"
zone="AZ_GENERAL"
tenantname="toon-plugin"
username="toonplugin"
password="Tp~!@tP689"
;;
qitoon)
vlanid="e62fedd3-33b9-40b4-8426-352cec552866"
source="qitoon"
zone="AZ_GENERAL"
tenantname="qitoon"
username="qitoon"
password="qitoon#123"
;;
search)
vlanid="7868651a-b65d-4406-9b9a-e4ecc3d7925d"
source="search"
zone="AZ_GENERAL"
tenantname="search"
username="search"
password="search#123"
;;
sysoper)
vlanid="151dfdec-4b55-4fed-a09b-ae589616cfd7"
source="sysoper"
zone="AZ_GENERAL"
tenantname="sysoper"
username="sysoper"
password="sysoper#123"
;;
toonapp)
vlanid="f16c9ab4-d04c-42d1-a49b-c7717b737999"
source="toonapp"
zone="AZ_GENERAL"
tenantname="toon-app"
username="toonapp"
password="Ta~!@tA731"
;;
lpzd)
vlanid="ac1dcf9b-7106-44fd-8471-809716b7fafd"
source="lpzd"
zone="AZ_GENERAL"
tenantname="lpzd"
username="lpzd"
password="lpzd#123"
;;
pay)
vlanid="560a1299-a15e-423a-ab6f-f9b882d448fe"
source="pay"
zone="AZ_GENERAL"
tenantname="pay"
username="pay"
password="pay#123"
;;
homesch)
vlanid="67216165-7ca5-4b59-909a-de56b0c2ba8f"
source="homesch"
zone="AZ_GENERAL"
tenantname="home-school"
username="homesch"
password="homesch#123"
;;
lhzf)
vlanid="9228d4fd-6b7e-417d-ae3e-196cbb3da253"
source="lhzf"
zone="AZ_GENERAL"
tenantname="lhzf"
username="lhzf"
password="lhzf#123"
;;
esac
source /root/$source
nova server-group-create test_mysas anti-affinity
nova server-group-create test_myssd anti-affinity
nova server-group-create test_lvs anti-affinity
#生产第一批虚机
nova boot BJDS --flavor prod-mysql-8C32G80G  --image mysqlssd-80G-20170627 --nic net-id=$vlanid --min-count 1 --max-count 2  --hint group=test_myssd --availability-zone $zone

#取得mysql虚机的name，第一个为主，第二个为从1
nova list|grep BJDS|awk -F "|" '{print $3}'|awk '{gsub(/ /,"")}1'>/tmp/host.txt 

#开始生产第三个mysql虚机，为sas盘的，需要更改镜像和flavor类型
nova boot BJDSW --flavor prod-mysql-8C32G80G  --image mysqlssd-80G-20170627 --nic net-id=$vlanid --min-count 1 --max-count 1  --hint group=test_myssd --availability-zone $zone

#取得第三个mysql个虚机的name
nova list|grep BJDSW|awk -F "|" '{print $3}'|awk '{gsub(/ /,"")}1'>>/tmp/host.txt 

#开始生产lvs虚机
nova boot BJDSWG --flavor apache_4C4G50G  --image mycat-50G-20170628 --nic net-id=$vlanid --min-count 1 --max-count 2  --hint group=test_lvs --availability-zone $zone

#取得lvs虚机的name
nova list|grep BJDSWG|awk -F "|" '{print $3}'|awk '{gsub(/ /,"")}1'>>/tmp/host.txt 

#取出第一个mysql name
name1=$(cat /tmp/host.txt |sed -n "1p")
#取出第二个msyql name
name2=$(cat /tmp/host.txt |sed -n "2p")
#取出第三个mysql name
name3=$(cat /tmp/host.txt |sed -n "3p")
#取出第一个lvs name
name4=$(cat /tmp/host.txt |sed -n "4p")
#取出第二个lvs name
name5=$(cat /tmp/host.txt |sed -n "5p")

#判断第一个虚机是否生产，生产后挂盘
  while true
            do
            state=$(nova show "$name1" | grep "vm_state"|awk -F "|" '{print $3}'|awk '{gsub(/ /,"")}1')
      if [ "$state"  ==  "active" ]; then
           echo "---------------------------------------------------------------------------------------"
           echo "--------------------------------create $name1 success!--------------------------------!!!!"
           echo "---------------------------------------------------------------------------------------"
		 #修改虚机名字
		 ip=$(nova list |grep -w "$name1"|awk -F "|" '{print $7}'|awk -F "=" '{print $2}'|awk '{gsub(/ /,"")}1')
		 echo $ip >/tmp/ipwg.txt
		 ip1=$(cat /tmp/ipwg.txt|awk -F "." '{print $4}')
		 rname=bjdx-prd-lh-mys-qq.sys.cn
                 nova rename $name1 bjdx-prd-lh-mys-qq.sys.cn
		 echo "$rname" >/tmp/mysql.txt
		 echo "$ip" >> /tmp/mysql.txt
#开始挂盘		  
          xujiid=$(nova list |grep -w "$rname"|awk -F "|" '{print $2}'|awk '{gsub(/ /,"")}1')
          tenantid=$(nova show $xujiid|grep tenant_id|awk -F "|" '{print $3}'|awk '{gsub(/ /,"")}1')
          curl -X POST -d  '{"auth": {"tenantName": "'"$tenantname"'", "passwordCredentials":{"username": "'"$username"'", "password": "'"$password"'"}}}' -H "Content-type: application/json" http://10.252.1.11:35357/v2.0/tokens | python -mjson.tool >/tmp/wg17.txt
          tokenid=$(cat /tmp/wg17.txt |sed -n '/issued_at/{x;p};h'|awk -F ":" '{print $2}'|sed  's/"//g'|awk -F "," '{print $1}'|awk '{gsub(/ /,"")}1')
          echo tenantid is：$tenantid
           sleep 1s
          echo xujiid is：$xujiid
           sleep 1s
          echo tokenid is：$tokenid
           sleep 1s
          echo "begin create yunpan"
           sleep 1s
          curl -i -X POST http://10.252.1.11:8776/v1/$tenantid/volumes -H "User-Agent: python-cinderclient" -H "Content-Type: application/json" -H "Accept: application/json" -H "X-Auth-Token: $tokenid" -d '{"volume": {"status": "creating", "availability_zone": "nova", "source_volid": null, "display_description": null, "snapshot_id": null, "user_id": null, "size": 200, "display_name": "'"$rname"'", "imageRef": null, "attach_status": "detached", "volume_type": null, "project_id": null, "metadata": {}, "lvm_instance_id":"'"$xujiid"'"}}'
           sleep 5s
           echo "----------------------------------attach yunpan---------------------------------"
          while true
          do
              yunpan_status=$(cinder list|grep -w "$rname"|awk -F "|" '{print $3}'|awk '{gsub(/ /,"")}1')
              yunpan=$(cinder list|grep -w "$rname"|awk -F "|" '{print $2}'|awk '{gsub(/ /,"")}1')
              if [ ${yunpan_status} == "available" ];then
                   nova volume-attach $rname $yunpan /dev/vdb
                   sleep 30s
                   yunpan_status=$(cinder list|grep -w "$rname"|awk '{print $6}')
                   echo "----- yunpan status is ${yunpan_status} --------"
                   break
              else
                   sleep 10s
              fi
          done
           break
           else
               sleep 20s
              echo "------------------------------keeping wait!-----------------------------------"
         fi
            done
			
#判断第二个虚机是否生产，生产后挂盘
 while true
            do
            state=$(nova show "$name2" | grep "vm_state"|awk -F "|" '{print $3}'|awk '{gsub(/ /,"")}1')
      if [ "$state"  ==  "active" ]; then
           echo "---------------------------------------------------------------------------------------"
           echo "--------------------------------create $name2 success!--------------------------------!!!!"
           echo "---------------------------------------------------------------------------------------"
		 #修改虚机名字
		 ip=$(nova list |grep -w "$name2"|awk -F "|" '{print $7}'|awk -F "=" '{print $2}'|awk '{gsub(/ /,"")}1')
		 echo $ip >/tmp/ipwg.txt
		 ip1=$(cat /tmp/ipwg.txt|awk -F "." '{print $4}')
		 rname=bjdx-prd-lh-mys-ww.sys.cn
                 nova rename $name2 bjdx-prd-lh-mys-ww.sys.cn
		 echo "$rname" >>/tmp/mysql.txt
		 echo "$ip" >> /tmp/mysql.txt
#开始挂盘		  
          xujiid=$(nova list |grep -w "$rname"|awk -F "|" '{print $2}'|awk '{gsub(/ /,"")}1')
          tenantid=$(nova show $xujiid|grep tenant_id|awk -F "|" '{print $3}'|awk '{gsub(/ /,"")}1')
          curl -X POST -d  '{"auth": {"tenantName": "'"$tenantname"'", "passwordCredentials":{"username": "'"$username"'", "password": "'"$password"'"}}}' -H "Content-type: application/json" http://10.252.1.11:35357/v2.0/tokens | python -mjson.tool >/tmp/wg17.txt
          tokenid=$(cat /tmp/wg17.txt |sed -n '/issued_at/{x;p};h'|awk -F ":" '{print $2}'|sed  's/"//g'|awk -F "," '{print $1}'|awk '{gsub(/ /,"")}1')
          echo tenantid is：$tenantid
           sleep 1s
          echo xujiid is：$xujiid
           sleep 1s
          echo tokenid is：$tokenid
           sleep 1s
          echo "begin create yunpan"
           sleep 1s
          curl -i -X POST http://10.252.1.11:8776/v1/$tenantid/volumes -H "User-Agent: python-cinderclient" -H "Content-Type: application/json" -H "Accept: application/json" -H "X-Auth-Token: $tokenid" -d '{"volume": {"status": "creating", "availability_zone": "nova", "source_volid": null, "display_description": null, "snapshot_id": null, "user_id": null, "size": 200, "display_name": "'"$rname"'", "imageRef": null, "attach_status": "detached", "volume_type": null, "project_id": null, "metadata": {}, "lvm_instance_id":"'"$xujiid"'"}}'
          sleep 5s
           echo "----------------------------------attach yunpan---------------------------------"
          while true
          do
              yunpan_status=$(cinder list|grep -w "$rname"|awk -F "|" '{print $3}'|awk '{gsub(/ /,"")}1')
              yunpan=$(cinder list|grep -w "$rname"|awk -F "|" '{print $2}'|awk '{gsub(/ /,"")}1')
              if [ ${yunpan_status} == "available" ];then
                   nova volume-attach $rname $yunpan /dev/vdb
                   sleep 30s
                   yunpan_status=$(cinder list|grep -w "$rname"|awk '{print $6}')
                   echo "----- yunpan status is ${yunpan_status} --------"
                   break
              else
                   sleep 10s
              fi
          done
           break
           else
               sleep 10s
              echo "------------------------------keeping wait!-----------------------------------"
             fi
            done
#判断第三个虚机是否生产，生产后挂盘
while true
            do
            state=$(nova show "$name3" | grep "vm_state"|awk -F "|" '{print $3}'|awk '{gsub(/ /,"")}1')
            if [ "$state"  ==  "active" ]; then
           echo "---------------------------------------------------------------------------------------"
           echo "--------------------------------create $name3 success!--------------------------------!!!!"
           echo "---------------------------------------------------------------------------------------"
		 #修改虚机名字
		 ip=$(nova list |grep -w "$name3"|awk -F "|" '{print $7}'|awk -F "=" '{print $2}'|awk '{gsub(/ /,"")}1')
		 echo $ip >/tmp/ipwg.txt
		 ip1=$(cat /tmp/ipwg.txt|awk -F "." '{print $4}')
		 rname=bjdx-prd-lh-mys-ee.sys.cn
                 nova rename $name3 bjdx-prd-lh-mys-ee.sys.cn
		 echo "$rname" >>/tmp/mysql.txt
		 echo "$ip" >> /tmp/mysql.txt
#开始挂盘		  
          xujiid=$(nova list |grep -w "$rname"|awk -F "|" '{print $2}'|awk '{gsub(/ /,"")}1')
          tenantid=$(nova show $xujiid|grep tenant_id|awk -F "|" '{print $3}'|awk '{gsub(/ /,"")}1')
          curl -X POST -d  '{"auth": {"tenantName": "'"$tenantname"'", "passwordCredentials":{"username": "'"$username"'", "password": "'"$password"'"}}}' -H "Content-type: application/json" http://10.252.1.11:35357/v2.0/tokens | python -mjson.tool >/tmp/wg17.txt
          tokenid=$(cat /tmp/wg17.txt |sed -n '/issued_at/{x;p};h'|awk -F ":" '{print $2}'|sed  's/"//g'|awk -F "," '{print $1}'|awk '{gsub(/ /,"")}1')
          echo tenantid is：$tenantid
           sleep 1s
          echo xujiid is：$xujiid
           sleep 1s
          echo tokenid is：$tokenid
           sleep 1s
          echo "begin create yunpan"
           sleep 1s
          curl -i -X POST http://10.252.1.11:8776/v1/$tenantid/volumes -H "User-Agent: python-cinderclient" -H "Content-Type: application/json" -H "Accept: application/json" -H "X-Auth-Token: $tokenid" -d '{"volume": {"status": "creating", "availability_zone": "nova", "source_volid": null, "display_description": null, "snapshot_id": null, "user_id": null, "size": 200, "display_name": "'"$rname"'", "imageRef": null, "attach_status": "detached", "volume_type": null, "project_id": null, "metadata": {}, "lvm_instance_id":"'"$xujiid"'"}}'
            sleep 5s
           echo "----------------------------------attach yunpan---------------------------------"
          while true
          do
              yunpan_status=$(cinder list|grep -w "$rname"|awk -F "|" '{print $3}'|awk '{gsub(/ /,"")}1')
              yunpan=$(cinder list|grep -w "$rname"|awk -F "|" '{print $2}'|awk '{gsub(/ /,"")}1')
              if [ ${yunpan_status} == "available" ];then
                   nova volume-attach $rname $yunpan /dev/vdb
                   sleep 30s
                   yunpan_status=$(cinder list|grep -w "$rname"|awk '{print $6}')
                   echo "----- yunpan status is ${yunpan_status} --------"
                   break
              else
                   sleep 10s
              fi
          done
           break
           else
               sleep 20s
              echo "------------------------------keeping wait!-----------------------------------"
         fi
            done

#判断第四个虚机是否生产
while true
            do
            state=$(nova show "$name4" | grep "vm_state"|awk -F "|" '{print $3}'|awk '{gsub(/ /,"")}1')
            if [ "$state"  ==  "active" ]; then
           echo "---------------------------------------------------------------------------------------"
           echo "--------------------------------create $name4 success!--------------------------------!!!!"
           echo "---------------------------------------------------------------------------------------"
		 #修改虚机名字
		 ip=$(nova list |grep -w "$name4"|awk -F "|" '{print $7}'|awk -F "=" '{print $2}'|awk '{gsub(/ /,"")}1')
		 echo $ip >/tmp/ipwg.txt
		 ip1=$(cat /tmp/ipwg.txt|awk -F "." '{print $4}')
		 rname=bjdx-prd-lh-lvs-rr.sys.cn
                 nova rename $name4 bjdx-prd-lh-lvs-rr.sys.cn
		 echo "$rname" >>/tmp/mysql.txt
		 echo "$ip" >> /tmp/mysql.txt

          break
           else
               sleep 20s
               echo "------------------------------keeping wait!-----------------------------------"
         fi
           done
		
while true
            do
            state=$(nova show "$name5" | grep "vm_state"|awk -F "|" '{print $3}'|awk '{gsub(/ /,"")}1')
            if [ "$state"  ==  "active" ]; then
           echo "---------------------------------------------------------------------------------------"
           echo "--------------------------------create $name4 success!--------------------------------!!!!"
           echo "---------------------------------------------------------------------------------------"
		 #修改虚机名字
		 ip=$(nova list |grep -w "$name5"|awk -F "|" '{print $7}'|awk -F "=" '{print $2}'|awk '{gsub(/ /,"")}1')
		 echo $ip >/tmp/ipwg.txt
		 ip1=$(cat /tmp/ipwg.txt|awk -F "." '{print $4}')
		 rname=bjdx-prd-lh-lvs-tt.sys.cn
                 nova rename $name5 bjdx-prd-lh-lvs-tt.sys.cn
		 echo "$rname" >>/tmp/mysql.txt
         	 echo "$ip" >> /tmp/mysql.txt

          break
           else
               sleep 20s
              echo "------------------------------keeping wait!-----------------------------------"
         fi
            done		
#删除server-group组
nova server-group-list > /tmp/groupwg.txt
mygroup=$(cat /tmp/groupwg.txt |grep -w "test_mysas"|awk -F "|" '{print $2}'|awk '{gsub(/ /,"")}1')
lvsgroup=$(cat /tmp/groupwg.txt |grep -w "test_myssd"|awk -F "|" '{print $2}'|awk '{gsub(/ /,"")}1')
lvsgroup1=$(cat /tmp/groupwg.txt |grep -w "test_lvs"|awk -F "|" '{print $2}'|awk '{gsub(/ /,"")}1')
nova server-group-delete $mygroup
nova server-group-delete $lvsgroup
nova server-group-delete $lvsgroup1

neutron port-create $vlanid >/tmp/vip.txt
vip1=$(cat /tmp/vip.txt |grep 10|awk -F ":" '{print $3}'| awk -F "}" '{print $1}'|sed 's/\"//g'|awk '{gsub(/ /,"")}1')
echo "rvip" >> /tmp/mysql.txt
echo "$vip1" >> /tmp/mysql.txt

neutron port-create $vlanid >/tmp/vip.txt
vip2=$(cat /tmp/vip.txt |grep 10|awk -F ":" '{print $3}'| awk -F "}" '{print $1}'|sed 's/\"//g'|awk '{gsub(/ /,"")}1')
echo "wvip" >> /tmp/mysql.txt
echo "$vip2" >> /tmp/mysql.txt

sleep 30s
