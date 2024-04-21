# vcs
version control system implementation (math&amp;cs spbu spring school)

## Supported commands:
1. init
```bash
vcs init
```
2. status
```bash
vcs status
```
3. add
```bash
vcs add <relpaths>
```
4. commit
```bash
vcs commit -m "<message>"
```
5. log
```bash
vcs log
```
6. reset
```bash
vcs reset <commit_hash>
```

## Installation
1. Download server and client
2. Build server
```bash
cd server
mkdir build
cd build
cmake ..
make
```
3. Run server
```bash
cd server
./bin/vcs-server <absolute path to folder where you want to store remote data>
```
4. Client – ???