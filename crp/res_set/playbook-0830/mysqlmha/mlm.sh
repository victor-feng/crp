#!/bin/bash
/bin/sh $1/masterip.sh $1
ansible -i $1/hosts  new-host -u root --private-key=$1/../old_id_rsa -m script -a $1/master2.sh

/bin/sh $1/slave1ip.sh $1
ansible -i $1/hosts  new-host -u root  --private-key=$1/../old_id_rsa -m script -a $1/slave11.sh

/bin/sh $1/slave2ip.sh $1
ansible -i $1/hosts  new-host -u root  --private-key=$1/../old_id_rsa -m script -a $1/slave22.sh

/bin/sh $1/lvs1ip.sh $1
ansible -i $1/hosts  new-host -u root  --private-key=$1/../old_id_rsa -m script -a $1/lvs11.sh

/bin/sh $1/lvs2ip.sh $1
ansible -i $1/hosts  new-host -u root  --private-key=$1/../old_id_rsa -m script -a $1/lvs22.sh
