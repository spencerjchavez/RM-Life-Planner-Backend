FROM python:3.9

ENV PYTHONPATH "${PYTHONPATH}:/app"

COPY requirements.txt /app/requirements.txt

RUN pip3 install --no-cache-dir --upgrade -r /app/requirements.txt

COPY ./app /app

EXPOSE 80

CMD ["uvicorn", "app.Routes:app", "--host", "0.0.0.0", "--port", "80"]
