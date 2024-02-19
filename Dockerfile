FROM python:3.9.16

ENV SRC_DIR /usr/src/

COPY . ${SRC_DIR}

RUN pip install -r ${SRC_DIR}/requirements.txt

WORKDIR ${SRC_DIR}

CMD [ "python", "./CTS_Scoreboard.py" ]
