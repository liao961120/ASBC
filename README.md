# ASBC query backend

API backend for [`liao961120/kwic`](https://github.com/liao961120/kwic)

## Run API

### Python

See `requirements.txt` for dependencies. After the dependencies are met, run: 

```bash
python3 main.py
```

The api would be served at `http://localhost:1420`.


### Docker

```bash
#docker run -p host:container -v host:container <image-name>
# Unix-like bash: cd to `data/` and run:
docker container run -it -p 127.0.0.1:1420:80 -v $(pwd):/usr/src/app/data/ asbc

# Windows cmd: cd to `data/` and run
docker container run -it -p 127.0.0.1:1420:80 -v %cd%:/usr/src/app/data/ asbc

# Windows PowerShell: cd to `data/` and run
docker container run -it -p 127.0.0.1:1420:80 -v ${PWD}:/usr/src/app/data/ asbc
```

The api would be served at `http://localhost:1420`.