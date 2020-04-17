# 2048-PyQt
Based on the popular game [2048](https://github.com/gabrielecirulli/2048) by Gabriele Cirulli.
The game's objective is to slide numbered tiles on a grid to combine them to create a tile with
 the number 2048. Here is Python version that uses PyQt5.  

![screenshot](screenshot.png)  

# Features
- Custom grid resolutions by changing following option  
(minimally supported is 4)
```ini
[Game]
grid = 4
```
- Save / load progress
- Animation support

# Usage
Make sure you have installed [Git](https://git-scm.com/downloads), 
[Python](https://wiki.python.org/moin/BeginnersGuide/Download) and
[pip3](https://pip.pypa.io/en/stable/) on your PC.  
Clone repository:
```shell script
git clone https://github.com/dex359/2048-PyQt.git
```  
Change folder:
```shell script
cd 2048-PyQt
```
Then install dependencies by following command:
```shell script
pip3 install -r requirements.txt
```
To run:
```shell script
python3 game.py
```
 or double click on 'game.py' in file explorer. On Linux you must before:
 ```shell script
chmod +x game.py
```