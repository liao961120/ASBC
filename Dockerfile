FROM python:3.7-alpine
WORKDIR /usr/src/app
COPY requirements.txt /usr/src/app
RUN apk add --no-cache python3-dev libstdc++ && \
    apk add --no-cache g++ && \
    ln -s /usr/include/locale.h /usr/include/xlocale.h && \
    pip3 install numpy && \
    pip3 install pandas
RUN pip install -r requirements.txt
RUN pip install gunicorn
COPY . /usr/src/app
EXPOSE 80
# Command to run when running docker run
CMD [ "gunicorn", "-b", "0.0.0.0:80", "main:app" ]
# docker build -t <tag-name> <path>
# docker build -t asbc .
# docker container run -it -p 127.0.0.1:1420:80 -v /home/liao/Desktop/ASBC/data/:/usr/src/app/data/ asbc

