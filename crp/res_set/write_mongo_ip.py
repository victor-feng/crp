# coding:utf-8
import sys


def write_mongo():
    print sys.argv
    if len(sys.argv) < 2:
        print 'please input the ip'
    try:
        master_ip = sys.argv[-1]
        slave1 = sys.argv[-2]
        slave2 = sys.argv[-3]
    except IndexError as e:
        print e
    with open('/tmp/mongo.txt', 'w') as f:
        f.write('%s\n' % 'mongomaster')
        f.write('%s\n' % master_ip)
        f.write('%s\n' % 'mongoslave1')
        f.write('%s\n' % slave1)
        f.write('%s\n' % 'mongoslave2')
        f.write('%s\n' % slave2)


if __name__ == '__main__':
    write_mongo()
