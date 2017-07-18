# coding:utf-8
import sys


def write_mongo():
    print sys.argv
    if len(sys.argv) < 2:
        print 'please input the ip'
    ip = sys.argv[1]
    with open('/tmp/mongo.txt', 'w') as f:
        f.write(ip)

if __name__ == '__main__':
    write_mongo()
