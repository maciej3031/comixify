FROM python:3.6

RUN mkdir /comixify
WORKDIR /comixify
COPY . /comixify
RUN pip install --upgrade pip && pip install -r requirements.txt

# Port to expose
EXPOSE 8080

ENTRYPOINT ["sh", "entrypoint.sh"]
CMD ['start']