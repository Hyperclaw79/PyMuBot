FROM python:3.6.4-alpine3.7

# install requirements
COPY src/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt


# copy current directory to /app
COPY . /app

# set app/src as the working directory
WORKDIR /app/src

# Run the python file
CMD ["python","-u","bot.py"]
