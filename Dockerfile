FROM python:3.9

ENV PYTHONPATH "${PYTHONPATH}:/app"

COPY requirements.txt ./requirements.txt

RUN pip3 install --no-cache-dir --upgrade -r ./requirements.txt
<<<<<<< HEAD
RUN pip3 install --no-cache-dir py-bcrypt
=======
RUN pip3 install --no-cache-dir py-bcrpyt
>>>>>>> 051ff938d4ee7fcd6f9aab14e2151c332c2ff40c

COPY ./app /app

EXPOSE 80

CMD ["uvicorn", "app.Routes:app", "--host", "0.0.0.0", "--port", "80"]
