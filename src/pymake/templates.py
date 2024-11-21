"""A collection of templates."""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict

TEMPLATE_ENVS = """
# This file is a suggestion. It may contain way to many or way to few secions and variables.
# Just add the variables you need.
# 
# But remember to place every(!) substituion variable in this file. 
# All of them!, and remember to remove this file from the production environment.
# If not, the concept of secrets becomes kind of pointless..
# All variables MUST be quoted! ie. TIMESTAMP: "null"
GENERAL:
  TIMESTAMP: ""
  COMPOSE_PROJECT_NAME: ""
  APP_NAME: ""
  APP_SOURCE_ROOT: ""
  APP_ROOT: ""
  APP_PORT: ""
  ALLOWED_HOSTS: ""
DJANGO:
  DJANGO_ENV: "DEBUG"
  DJANGO_SU_NAME: ""
  DJANGO_SU_EMAIL: ""
  DJANGO_SU_PASSWORD: ""
  DJANGO_SECRET: ""
  DJANGO_DB_USER: ""
  DJANGO_DB_PASSWORD: ""
  DJANGO_DB_PORT: ""
  DJANGO_SETTINGS_MODULE: "${APP_NAME}"
  DJANGO_DB_NAME: "${APP_NAME}"
  DJANGO_DB: "${APP_NAME}"
  DJANGO_DB_HOST: "${APP_NAME}"
POSTGRES:
  POSTGRES_DB: "${APP_NAME}"
  POSTGRES_USER: "${DJANGO_DB_USER}"
  POSTGRES_PASSWORD: "${DJANGO_DB_PASSWORD}"
  POSTGRES_DB_PORT: "${DJANGO_DB_PORT}"
  PGPASSWORD: "${DJANGO_DB_PASSWORD}"
  POSTGRES_VERSION: "docker.io/library/postgres:latest"
  POSTGRES_MOUNT: "/var/lib/postgresql/data"
MICROSOFT: # Single Sign on
  MICROSOFT_AUTH_CLIENT_ID: ""
  MICROSOFT_AUTH_CLIENT_SECRET: ""
  MICROSOFT_AUTH_TENANT_ID: "" 
  MICROSOFT_AUTH_EXTRA_SCOPES: "User.Read"
BUSINESS_CENTRAL:
  BCENTRAL_CLIENT_ID: ""
  BCENTRAL_CLIENT_SECRET: ""
  BCENTRAL_TENANT_ID: ""
  BCENTRAL_ENVIRONMENT: ""
  BCENTRAL_API_URL: "https://api.businesscentral.dynamics.com/v2.0/${BCENTRAL_TENANT_ID}/${BCENTRAL_ENVIRONMENT}/api/v2.0/"
  BCENTRAL_PAYMENT_TERMS_API_URL: "https://api.businesscentral.dynamics.com/v2.0/${BCENTRAL_TENANT_ID}/${BCENTRAL_ENVIRONMENT}/api/v2.0/"
  BCENTRAL_TOKEN_URL: "https://login.microsoftonline.com/${BCENTRAL_TENANT_ID}/oauth2/v2.0/token"
  BCENTRAL_COMPANY: ""
  BCENTRAL_RESOURCE: "/api/v2.0/companies(${BCENTRAL_COMPANY})/"
NGINX:
  WORKER_PROCESSES: "5"
  WORKER_RLIMIT_NOFILE: "8192"
  WORKER_CONNECTIONS: "101024"
  NGINX_IMAGE_VERSION: "latest"
GUNICORN:
  GUNICORN_LOG_LEVEL: "info"
  GUNICORN_WORKERS: "2"
  GUNICORN_TIMEOUT: "90"
  GUNICORN_RELOAD: "reload" # When debugging, use reload.
MEMCACHED:
  MEMCACHED_PORT: "11211"
  MEMCACHED_LOCATION: "${APP_NAME}-memcached:${MEMCACHED_PORT}"
  MEMCACHED_IMAGE_VERSION: "latest"
SERVICE_NAMES:
  APPSERVICE_NAME: "${APP_NAME}-app"
  PROXYSERVICE_NAME: "${APP_NAME}-nginx"
  DBSERVICE_NAME: "${APP_NAME}" # must be the same as the database name!
  MEMCACHED_NAME: "${APP_NAME}-memcached"
CONFIGFILE:
  IMAGE: "3.12-bullseye"
  USER: "${APP_NAME}"
PODMAN_CONTAINER_NAMES:
  APPSERVICE_CONTAINER_NAME: "container_name: ${COMPOSE_PROJECT_NAME}_${APPSERVICE_NAME}"
  PROXYSERVICE_CONTAINER_NAME: "container_name: ${COMPOSE_PROJECT_NAME}_${PROXYSERVICE_NAME}"
  DBSERVICE_CONTAINER_NAME: "container_name: ${COMPOSE_PROJECT_NAME}_${DBSERVICE_NAME}"
  MEMCACHED_CONTAINER_NAME: "container_name: ${COMPOSE_PROJECT_NAME}_${MEMCACHED_NAME}"
SERVICE_VOLUMES:
  VOLUME_NAME: "${APP_NAME}"
  VOLUME_PREFIX: "${COMPOSE_PROJECT_NAME}"
"""

CONTAINERFILE_TEMPLATE = """
FROM python:${IMAGE}

ENV PYTHONUNBUFFERED=1

ENV PYTHONFAULTHANDLER=1

ENV PATH="/root/.local/bin/:${PATH}"

ENV PIP_ROOT_USER_ACTION=ignore

RUN apt-get update && apt-get install -y \
  vim

WORKDIR /opt/services/${VOLUME_PREFIX}${VOLUME_NAME}/src

RUN mkdir /opt/services/${VOLUME_PREFIX}${VOLUME_NAME}/static
VOLUME /opt/services/${VOLUME_PREFIX}${VOLUME_NAME}/static

RUN mkdir /opt/services/${VOLUME_PREFIX}${VOLUME_NAME}/media
VOLUME /opt/services/${VOLUME_PREFIX}${VOLUME_NAME}/media

COPY pyproject.toml .
COPY README.md .
COPY ${APP_NAME}/__about__.py ./${APP_NAME}/__about__.py 

RUN pip install --user --upgrade pip
RUN pip install --user --upgrade setuptools
RUN pip install --user .
"""

PLAY_KUBE_TEMPLATE = """
# Warning:
# All edits must happen in play-kube-template.yml
# Any edit made in the resulting play-kube.yml will be lost
#
# Save the output of this file and use kubectl create -f to import
# it into Kubernetes.
#
# Created with podman-4.4.2

# NOTE: If you generated this yaml from an unprivileged and rootless podman container on an SELinux
# enabled system, check the podman generate kube man page for steps to follow to ensure that your pod/container
# has the right permissions to access the volumes added.
---
apiVersion: v1
kind: Pod
metadata:
  creationTimestamp: ${TIMESTAMP}
  labels:
    app: ${APP_NAME}-pod
  name: ${APP_NAME}-pod
spec:
  containers:
    ## POSTGRESQL
    - name: ${DBSERVICE_NAME}
      args:
        - postgres
      env:
        - name: POSTGRES_DB
          valueFrom:
            configMapKeyRef:
              name: postgres-env
              key: POSTGRES_DB
        - name: POSTGRES_USER
          valueFrom:
            configMapKeyRef:
              name: postgres-env
              key: POSTGRES_USER
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: POSTGRES_PASSWORD
      image: ${POSTGRES_VERSION}
      ports:
        - name: postgresql
          containerPort: ${POSTGRES_DB_PORT}
      livenessProbe:
        exec:
          command:
            - /bin/sh
            - -c
            - exec pg_isready -d ${POSTGRES_DB} -U ${POSTGRES_USER} -h 127.0.0.1 -p ${POSTGRES_DB_PORT}
        failureThreshold: 6
        initialDelaySeconds: 30
        periodSeconds: 10
        successThreshold: 2
        timeoutSeconds: 5
      volumeMounts:
        - mountPath: ${POSTGRES_MOUNT}
          name: ${DBSERVICE_NAME}-volume-pvc
      resources:
        limits:
          memory: 2000000Ki
    ## MEMCACHED
    - name: ${MEMCACHED_NAME}
      args:
        - /opt/bitnami/scripts/memcached/run.sh
      image: ${MEMCACHED_IMAGE_VERSION}
      ports:
        - containerPort: ${MEMCACHED_PORT}
      securityContext:
        runAsNonRoot: true
      resources:
        limits:
          memory: 500000Ki
    ## DJANGO
    - name: ${APPSERVICE_NAME}
      args:
        - gunicorn
        - -c
        - config/gunicorn/gunicorn.conf
        - --chdir
        - ${APP_ROOT}
        - --bind
        - :${APP_PORT}
        - ${APP_ROOT}.wsgi:application
        - ${GUNICORN_RELOAD}
      command:
        - /bin/sh
        - /opt/services/${VOLUME_PREFIX}${VOLUME_NAME}/src/entrypoint.sh
      env:
        - name: DJANGO_ENV
          valueFrom:
            configMapKeyRef:
              name: django-env
              key: DJANGO_ENV
        - name: ALLOWED_HOSTS
          valueFrom:
            configMapKeyRef:
              name: django-env
              key: ALLOWED_HOSTS
        - name: DJANGO_DB
          valueFrom:
            configMapKeyRef:
              name: django-env
              key: DJANGO_DB
        - name: DJANGO_DB_USER
          valueFrom:
            configMapKeyRef:
              name: django-env
              key: DJANGO_DB_USER
        - name: DJANGO_DB_HOST
          valueFrom:
            configMapKeyRef:
              name: django-env
              key: DJANGO_DB_HOST
        - name: DJANGO_DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: django-credentials
              key: DJANGO_DB_PASSWORD
        - name: DJANGO_DB_PORT
          valueFrom:
            configMapKeyRef:
              name: django-env
              key: DJANGO_DB_PORT
        - name: DJANGO_SECRET
          valueFrom:
            secretKeyRef:
              name: django-credentials
              key: DJANGO_SECRET
        - name: DJANGO_SETTINGS_MODULE
          valueFrom:
            configMapKeyRef:
              name: django-env
              key: DJANGO_SETTINGS_MODULE
        # MEMCACHED
        - name: MEMCACHED_LOCATION
          valueFrom:
            configMapKeyRef:
              name: django-env
              key: MEMCACHED_LOCATION
        - name: MEMCACHED_PORT
          valueFrom:
            configMapKeyRef:
              name: django-env
              key: MEMCACHED_PORT
        # BCENTRAL
        - name: BCENTRAL_TOKEN_URL
          valueFrom:
            configMapKeyRef:
              name: django-env
              key: BCENTRAL_TOKEN_URL
        - name: BCENTRAL_RESOURCE
          valueFrom:
            configMapKeyRef:
              name: django-env
              key: BCENTRAL_RESOURCE
        - name: BCENTRAL_CLIENT_SECRET
          valueFrom:
            secretKeyRef:
              name: django-credentials
              key: BCENTRAL_CLIENT_SECRET
        - name: BCENTRAL_API_URL
          valueFrom:
            configMapKeyRef:
              name: django-env
              key: BCENTRAL_API_URL
        - name: BCENTRAL_COMPANY
          valueFrom:
            configMapKeyRef:
              name: django-env
              key: BCENTRAL_COMPANY
        - name: BCENTRAL_PAYMENT_TERMS_API_URL
          valueFrom:
            configMapKeyRef:
              name: django-env
              key: BCENTRAL_PAYMENT_TERMS_API_URL
        - name: BCENTRAL_TENANT_ID
          valueFrom:
            configMapKeyRef:
              name: django-env
              key: BCENTRAL_TENANT_ID
        - name: BCENTRAL_CLIENT_ID
          valueFrom:
            configMapKeyRef:
              name: django-env
              key: BCENTRAL_CLIENT_ID
        # GRAPHAPI
        - name: GRAPHAPI_TENANT_ID
          valueFrom:
            configMapKeyRef:
              name: django-env
              key: GRAPHAPI_TENANT_ID
        - name: GRAPHAPI_CLIENT_ID
          valueFrom:
            configMapKeyRef:
              name: django-env
              key: GRAPHAPI_CLIENT_ID
        - name: GRAPHAPI_CLIENT_SECRET
          valueFrom:
            secretKeyRef:
              name: django-credentials
              key: GRAPHAPI_CLIENT_SECRET
        # PARTNER API
        - name: PARTNER_CLIENT_ID
          valueFrom:
            configMapKeyRef:
              name: django-env
              key: PARTNER_CLIENT_ID
        - name: PARTNER_CLIENT_SECRET
          valueFrom:
            secretKeyRef:
              name: django-credentials
              key: PARTNER_CLIENT_SECRET
        - name: PARTNER_TENANT_ID
          valueFrom:
            configMapKeyRef:
              name: django-env
              key: PARTNER_TENANT_ID
        - name: PARTNER_PRICE_SHEET
          valueFrom:
            configMapKeyRef:
              name: django-env
              key: PARTNER_PRICE_SHEET
        - name: PARTNER_REDIRECT_URI
          valueFrom:
            configMapKeyRef:
              name: django-env
              key: PARTNER_REDIRECT_URI
        # MICROSOFT
        - name: MICROSOFT_AUTH_EXTRA_SCOPES
          valueFrom:
            configMapKeyRef:
              name: django-env
              key: MICROSOFT_AUTH_EXTRA_SCOPES
        - name: MICROSOFT_AUTH_TENANT_ID
          valueFrom:
            configMapKeyRef:
              name: django-env
              key: MICROSOFT_AUTH_TENANT_ID
        - name: MICROSOFT_AUTH_CLIENT_SECRET
          valueFrom:
            secretKeyRef:
              name: django-credentials
              key: MICROSOFT_AUTH_CLIENT_SECRET
        - name: MICROSOFT_AUTH_CLIENT_ID
          valueFrom:
            configMapKeyRef:
              name: django-env
              key: MICROSOFT_AUTH_CLIENT_ID
      image: localhost/${APPSERVICE_NAME}:latest
      ports:
        - containerPort: ${APP_PORT}
          hostPort: 33433
      readinessProbe:
        httpGet:
          path: "/"
          port: ${APP_PORT}
        initialDelaySeconds: 30
        periodSeconds: 10
        successThreshold: 1
      resources:
        limits:
          memory: 2000000Ki
      securityContext:
        runAsNonRoot: true
      stdin: true
      tty: true
      volumeMounts:
        - mountPath: /opt/services/${VOLUME_PREFIX}${VOLUME_NAME}/src:Z
          name: ${APP_NAME}-host-0
        - mountPath: /opt/services/${VOLUME_PREFIX}${VOLUME_NAME}/static:Z
          name: ${VOLUME_NAME}-static-volume-pvc
        - mountPath: /opt/services/${VOLUME_PREFIX}${VOLUME_NAME}/media:Z
          name: ${VOLUME_NAME}-media-volume-pvc
    # ## NGINX
    - name: ${PROXYSERVICE_NAME}
      args:
        - nginx
        - -g
        - daemon off;
      image: ${NGINX_IMAGE_VERSION}
      ports:
        - name: http
          containerPort: 80
          hostPort: ${APP_PORT}
      livenessProbe:
        httpGet:
          path: "/"
          port: ${APP_PORT}
        initialDelaySeconds: 30
        periodSeconds: 10
      readinessProbe:
        httpGet:
          path: "/"
          port: ${APP_PORT}
        failureThreshold: 6
        initialDelaySeconds: 30
        periodSeconds: 10
        successThreshold: 1
        timeoutSeconds: 5
      resources:
        limits:
          memory: 500000Ki
      securityContext:
        runAsNonRoot: true
        seLinuxOptions:
          type: spc_t
      volumeMounts:
        - mountPath: /etc/nginx/nginx.conf:Z
          name: ${PROXYSERVICE_NAME}.conf-host-0
          readOnly: true
        - mountPath: /etc/nginx/conf.d:Z
          name: ${PROXYSERVICE_NAME}-conf.d-host-1
        - mountPath: /opt/services/${VOLUME_PREFIX}${VOLUME_NAME}/static:Z
          name: ${VOLUME_NAME}-static-volume-pvc
        - mountPath: /opt/services/${VOLUME_PREFIX}${VOLUME_NAME}/media:Z
          name: ${VOLUME_NAME}-media-volume-pvc
  restartPolicy: Always
  volumes:
    - name: ${DBSERVICE_NAME}-volume-pvc
      persistentVolumeClaim:
        claimName: ${DBSERVICE_NAME}-volume
    - hostPath:
        path: ${APP_SOURCE_ROOT}
        type: Directory
      name: ${VOLUME_NAME}-host-0
    - name: ${VOLUME_NAME}-static-volume-pvc
      persistentVolumeClaim:
        claimName: ${VOLUME_NAME}-static-volume
    - name: ${VOLUME_NAME}-media-volume-pvc
      persistentVolumeClaim:
        claimName: ${VOLUME_NAME}-media-volume
    - hostPath:
        path: ${APP_SOURCE_ROOT}/config/nginx/nginx.conf
        type: File
      name: ${PROXYSERVICE_NAME}.conf-host-0
    - hostPath:
        path: ${APP_SOURCE_ROOT}/config/nginx/conf.d
        type: Directory
      name: ${PROXYSERVICE_NAME}-conf.d-host-1
"""

ENTRYPOINT_TEMPLATE = """
#! /bin/bash -x

python ${APP_NAME}/manage.py migrate --no-input || exit 1
python ${APP_NAME}/manage.py collectstatic --no-input || exit 1
exec "$@"
"""

GUNICORN_TEMPLATE = """
name = '${APP_NAME}'
loglevel = '${GUNICORN_LOG_LEVEL}'
errorlog = '-'
accesslog = '-'
workers = ${GUNICORN_WORKERS}
timeout = ${GUNICORN_TIMEOUT}
"""
NGINX_TEMPLATE_CONFIG = """
user  nginx;
worker_processes  ${WORKER_PROCESSES};

error_log  /var/log/nginx/error.log warn;
pid        /var/run/nginx.pid;

worker_rlimit_nofile  ${WORKER_RLIMIT_NOFILE};

events {
    worker_connections  ${WORKER_CONNECTIONS};
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';

    access_log  /var/log/nginx/access.log  main;

    sendfile        on;
    #tcp_nopush     on;

    keepalive_timeout  65;
    proxy_read_timeout 300;
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
    #gzip  on;

    include /etc/nginx/conf.d/*.conf;
}
"""

NGINX_TEMPLATE_LOCAL = """
# first we declare our upstream server, which is our Gunicorn application
upstream ${APPSERVICE_NAME}_${APP_NAME} {
    # docker will automatically resolve this to the correct address
    # because we use the same name as the service: "djangoapp"
    server ${APPSERVICE_NAME}:${APP_PORT};
}

# now we declare our main server
server {

    listen 80;
    server_name localhost;

    location /static/ {
         alias /opt/services/${VOLUME_PREFIX}${VOLUME_NAME}/static/;
    }

    location /media/ {
         alias /opt/services/${VOLUME_PREFIX}${VOLUME_NAME}/media/;
    }


    location / {
        root /opt/services/${VOLUME_PREFIX}${VOLUME_NAME}/static/;
        try_files /maintenance/maintenance.html @proxy;
    }

    location @proxy {
        # everything is passed to Gunicorn
        set $myscheme "https";
        client_max_body_size 2M;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $myscheme;
        proxy_redirect off;
        proxy_pass http://${APPSERVICE_NAME}_${APP_NAME};
    }
}
"""

DJANGO_CONFIGMAP = """
apiVersion: v1
data:
  DJANGO_ENV: ${DJANGO_ENV}
  ALLOWED_HOSTS: "${ALLOWED_HOSTS}"
  DJANGO_DB_USER: ${DJANGO_DB_USER}
  DJANGO_DB: ${DJANGO_DB}
  DJANGO_DB_HOST: ${DJANGO_DB_HOST}
  DJANGO_DB_PORT: ${DJANGO_DB_PORT}
  DJANGO_SETTINGS_MODULE: ${DJANGO_SETTINGS_MODULE}
  BCENTRAL_TOKEN_URL: ${BCENTRAL_TOKEN_URL}
  BCENTRAL_RESOURCE: ${BCENTRAL_RESOURCE}
  BCENTRAL_API_URL: ${BCENTRAL_API_URL}
  BCENTRAL_COMPANY: ${BCENTRAL_COMPANY}
  BCENTRAL_PAYMENT_TERMS_API_URL: ${BCENTRAL_PAYMENT_TERMS_API_URL}
  BCENTRAL_TENANT_ID: ${BCENTRAL_TENANT_ID}
  BCENTRAL_CLIENT_ID: ${BCENTRAL_CLIENT_ID}
  MICROSOFT_AUTH_EXTRA_SCOPES: ${MICROSOFT_AUTH_EXTRA_SCOPES}
  MICROSOFT_AUTH_TENANT_ID: ${MICROSOFT_AUTH_TENANT_ID}
  MICROSOFT_AUTH_CLIENT_ID: ${MICROSOFT_AUTH_CLIENT_ID}
  MEMCACHED_LOCATION: ${MEMCACHED_LOCATION}
  MEMCACHED_PORT: "${MEMCACHED_PORT}"
kind: ConfigMap
metadata:
  name: django-env
"""

POSTGRES_CONFIGMAP = """
apiVersion: v1
data:
  POSTGRES_DB: ${POSTGRES_DB}
  POSTGRES_USER: ${POSTGRES_USER}
kind: ConfigMap
metadata:
  name: postgres-env
"""

DJANGO_SECRET = """
apiVersion: v1
data:
  DJANGO_SECRET: ${DJANGO_SECRET}
  DJANGO_DB_PASSWORD: ${DJANGO_DB_PASSWORD}
  BCENTRAL_CLIENT_SECRET: ${BCENTRAL_CLIENT_SECRET}
  MICROSOFT_AUTH_CLIENT_SECRET: ${MICROSOFT_AUTH_CLIENT_SECRET}
kind: Secret
metadata:
  creationTimestamp: null
  name: django-credentials
"""

POSTGRES_SECRET = """
apiVersion: v1
data:
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
kind: Secret
metadata:
  creationTimestamp: null
  name: postgres-credentials
"""

PATHS = {
    "config": Path("./config"),
    "templates": Path("./config/templates"),
    "gunicorn-out": Path("./config/gunicorn"),
    "nginx-out": Path("./config/nginx"),
    "conf.d-out": Path("./config/nginx/conf.d"),
    "secrets": Path("./config/templates/secrets"),
    "secrets-out": Path("./secrets"),
    "configmaps": Path("./config/templates/configmaps"),
    "configmaps-out": Path("./configmaps"),
}


class TemplateType(TypedDict):
    data: str
    templatefile: Path
    parsedfile: Path
    remove: bool


DEFAULT_ENV_FILE = Path("./config/templates/template-envs.yaml")

TEMPLATES: list[TemplateType] = [
    {
        "data": TEMPLATE_ENVS,
        "templatefile": PATHS["templates"] / "template-envs.yaml",
        "parsedfile": PATHS["templates"] / "template-envs.yaml",
        "remove": False,
    },
    {
        "data": CONTAINERFILE_TEMPLATE,
        "templatefile": PATHS["templates"] / "Containerfile-template",
        "parsedfile": Path("./Containerfile"),
        "remove": False,
    },
    {
        "data": PLAY_KUBE_TEMPLATE,
        "templatefile": PATHS["templates"] / "play-kube-template.yaml",
        "parsedfile": Path("./play-kube.yaml"),
        "remove": False,
    },
    {
        "data": ENTRYPOINT_TEMPLATE,
        "templatefile": PATHS["templates"] / "entrypoint-template",
        "parsedfile": Path("./entrypoint.sh"),
        "remove": False,
    },
    {
        "data": GUNICORN_TEMPLATE,
        "templatefile": PATHS["templates"] / "gunicorn-template.conf",
        "parsedfile": PATHS["gunicorn-out"] / "gunicorn.conf",
        "remove": False,
    },
    {
        "data": NGINX_TEMPLATE_CONFIG,
        "templatefile": PATHS["templates"] / "nginx-template.conf",
        "parsedfile": PATHS["nginx-out"] / "nginx.conf",
        "remove": False,
    },
    {
        "data": NGINX_TEMPLATE_LOCAL,
        "templatefile": PATHS["templates"] / "nginx-template-local.conf",
        "parsedfile": PATHS["conf.d-out"] / "local.conf",
        "remove": False,
    },
    {
        "data": DJANGO_CONFIGMAP,
        "templatefile": PATHS["configmaps"] / "django-env-map-template.yaml",
        "parsedfile": PATHS["configmaps-out"] / "django-env-map.yaml",
        "remove": False,
    },
    {
        "data": POSTGRES_CONFIGMAP,
        "templatefile": PATHS["configmaps"] / "postgres-env-map-template.yaml",
        "parsedfile": PATHS["configmaps-out"] / "postgres-env-map.yaml",
        "remove": False,
    },
    {
        "data": DJANGO_SECRET,
        "templatefile": PATHS["secrets"] / "django-secrets-template.yaml",
        "parsedfile": PATHS["secrets-out"] / "django-secrets-template.yaml",
        "remove": True,
    },
    {
        "data": POSTGRES_SECRET,
        "templatefile": PATHS["secrets"] / "postgres-secrets-template.yaml",
        "parsedfile": PATHS["secrets-out"] / "postgres-secrets-template.yaml",
        "remove": True,
    },
]
