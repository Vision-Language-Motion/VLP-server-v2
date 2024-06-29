ARG PYTORCH="1.8.1"
ARG CUDA="10.2"
ARG CUDNN="7"

FROM pytorch/pytorch:${PYTORCH}-cuda${CUDA}-cudnn${CUDNN}-devel
ARG AUTH_PASSWORD
ARG DO_DATABASE_PASSWORD
ARG GOOGLE_DEV_API_KEY=""
ARG RAPIDAPI_KEY=""
ARG DEBUG="True"
ENV DO_DATABASE_PASSWORD=$DO_DATABASE_PASSWORD
ENV AUTH_PASSWORD=$AUTH_PASSWORD
ENV GOOGLE_DEV_API_KEY=$GOOGLE_DEV_API_KEY
ENV RAPIDAPI_KEY = $RAPIDAPI_KEY
ENV DEBUG=$DEBUG



# To fix GPG key error when running apt-get update
RUN rm /etc/apt/sources.list.d/cuda.list \
    && rm /etc/apt/sources.list.d/nvidia-ml.list \
    && apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/3bf863cc.pub \
    && apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/machine-learning/repos/ubuntu1804/x86_64/7fa2af80.pub

# Install system dependencies for opencv-python
RUN apt-get update && apt-get install -y libgl1 libglib2.0-0 python-psycopg2 redis-server \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install mmcv
ARG MMCV=""
RUN if [ "${MMCV}" = "" ]; then pip install -U openmim && mim install 'mmcv>=2.0.0rc1' && mim install mmpose; else pip install -U openmim && mim install mmcv==${MMCV} && mim install mmpose; fi

# Verify the installation
RUN python -c 'import mmcv;print(mmcv.__version__)'

RUN pip install importlib-metadata==4.13.0

RUN pip install Django djangorestframework python-dotenv gunicorn psycopg2-binary whitenoise celery==5.1.0 django-celery-beat redis yt-dlp moviepy scenedetect google-api-python-client




# Add the rest of the code
COPY . /code/

# Make port 8000 available to the world outside this container
EXPOSE 8000

WORKDIR /code/vlp

#RUN redis-server --daemonize yes

# RUN celery -A server worker -l info


RUN python manage.py makemigrations && python manage.py migrate

RUN python manage.py collectstatic --noinput


#COPY start_docker.sh /code/start_docker.sh
RUN chmod +x /code/start_docker.sh

# CMD ["gunicorn", "--bind", "0.0.0.0:8000", "server.wsgi:application"]

ARG TEST="false"
RUN if [ "${TEST}" = "true" ]; then python manage.py test --noinput --keepdb; fi

# Comment this out if you're just testing
CMD ["/code/start_docker.sh"] 
