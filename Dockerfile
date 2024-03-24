# Pull the base image with python 3.8 as a runtime for your Lambda
FROM public.ecr.aws/lambda/python:3.9

COPY requirements.txt ./
RUN python3.9 -m pip install -r requirements.txt

# Copy python scripts
COPY app.py ./

# Set the CMD to your handler
CMD ["app.handler"]