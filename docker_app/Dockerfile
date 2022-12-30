FROM python:3

# COPY sample_three_player_sheet.csv .
# COPY requirements.txt .
# COPY docker_app/*.py .
# COPY docker_app/classes/*.py ./classes
COPY . .

# WORKDIR docker_app/

RUN pip install -r requirements.txt

CMD ["python", "main.py", "-fs"]
