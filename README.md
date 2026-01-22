# Forum

## Setup the app

1. Clone the repo by:
```sh
git clone https://github.com/kd51014/ai-project.git
```
2. Create .env file in repo directory, (check (.env.example) for example). File must contain:
```txt
SECRET_KEY=
ADMIN_PASSWORD=
```

### By docker
3. Build docker image by:
```sh
docker build . -t forum-app:latest
```

4. Run docker container, by
```sh
docker run -d -p 80:80 forum-app:latest
```

5. Visit http://localhost:80 and enjoy :)

### By python
#### Note: Steps 3,4 & 6 may depend on your system, in case of any issues, please visit: https://docs.python.org/3/library/venv.html
3. Create virtual environment, by: 
```sh
python3 -m venv .venv
```

4. Activate newly created virtual environment, by:
```sh
source ./.venv/bin/activate
```

5. Install the python dependencies, by
```sh
pip install -r requirements.txt
```

6. Run the app, by:
```sh 
python3 run.py
```

7. Visit http://localhost:5000 and enjoy :)
