FROM python:3

RUN mkdir -p /docker_app
COPY sample_one_player_sheet.csv docker_app/
COPY requirements.txt docker_app/
COPY docker_app/* docker_app/

WORKDIR /docker_app

RUN pip install -r requirements.txt

CMD ["python", "main.py", "-t"]
