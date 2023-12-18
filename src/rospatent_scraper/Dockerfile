FROM python:3.9-slim

WORKDIR /opt/app-root/src/

COPY src/rospatent_scraper/requirements.txt /opt/app-root/src/rospatent_scraper/

RUN pip install --no-cache-dir -r /opt/app-root/src/rospatent_scraper/requirements.txt

ENV PYTHONPATH /opt/app-root/src
ENV PYTHONUNBUFFERED=1

CMD ["gunicorn", "--config", "/opt/app-root/src/rospatent_scraper/api/config/gunicorn.conf.py"]