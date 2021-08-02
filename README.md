# Mortgage Calculator API

coverage run --source=./app -m unittest discover -s app -p 'test_*.py'

## 1. PyCharm with virtualenv (development)

### 1.1. Add service as a project to PyCharm

Open Terminal in the project folder and execute:

```shell
python3 -m venv /venv
source venv/bin/activate
pip install -r app/requirements.txt
export FLASK_APP=app/app.py
```
Set default interpreter in the venv folder.\
Set default testing framework Unittest.\
Reopen the project from scratch.\

### 1.2. Launch service

Run unittest in the "tests" folder.

In the Terminal execute:

```shell
flask run
```

Open link in the browser: **localhost:5000.**\
It should have text: **«Hello World! I'm Mortgage Calculator, version X.X.X»**.\
Open Postman, load Mortgage Calculator collection and run all requests one by one.\
Then make work "mortgage-calculator-web" service

## 2. Run service with Docker on a local machine

Launch docker on your machine!
Description in progress.

## 3. Run service with Docker Compose on a local machine

Launch docker on your machine!
Navigate into the folder, where **README.MD** file lays.
Duplicate **env.sample** file with new name **env**.
In the Terminal execute:
```shell
docker-compose up
```
Open link in the browser: **localhost:5000.**











# AMC-API

API for **Advanced (Awesome) Mortgage Calculator**

Python Flask application implements business-logic and API, connected to Forecaster to Google Database.

## Prerequisites

- Install Docker

## Steps

1. Clone project from GitHub
2. Copy **config.sample** file and rename copy into **config**
3. Open **Terminal** or something like that
4. Navigate into the folder where **README.md** file lays

```powershell
cd /project-folder
```

5. Run:

```powershell
docker build -t name-of-the-project .
```

6. Then run:

```powershell
docker run -dp 5000:5000 --env-file config name-of-the-project
```

Or run with the volume, so you will be able to change some code on the run:
**src** folder will be connected to the container's **src** folder except of the **\__pycache__** folder, it will create be created on your machine, but without any file there:

```powershell
docker run -dp 5000:5000 --env-file config -v ${PWD}/src:/app/src -v pycache:/app/src/__pycache__ name-of-the-project
```

7. Open link:

http://localhost:5000