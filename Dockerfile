FROM debian:bookworm-slim

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y \
    apache2 \
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    libmariadb-dev \
    libapache2-mod-wsgi-py3 \
    pkg-config \
    gcc 

# Configure timezone
ENV TZ=America/Mexico_City
RUN ln -snf  /etc/l/usr/share/zoneinfo/$TZocaltime && echo $TZ > /etc/timezone



COPY ./requirements.txt /app/

WORKDIR /app

RUN python3 -m venv /env
ENV PATH=$PATH:/env/bin/


#RUN mkdir /app/media && chown :www-data /app/media -R && chmod 775 /app/media -R
RUN /env/bin/pip install --upgrade pip

RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz-subset0 \
    libjpeg-dev \
    libopenjp2-7-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

RUN /env/bin/pip install -r /app/requirements.txt


CMD ["apachectl", "-D", "FOREGROUND"]