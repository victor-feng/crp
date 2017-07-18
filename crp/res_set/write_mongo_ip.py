# coding:utf-8
import sys


def write_mongo():
    print sys.argv
    ip = sys.argv[2]
    with open('/tmp/mongo.txt', 'w') as f:
        f.write(ip)

if __name__ == '__main__':
    write_mongo()
