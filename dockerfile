# use lite python image
FROM python:3.11-slim

# set work directory
WORKDIR /app

# install system dependensice
RUN apt-get update && apt-get install -y \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# copy requirments file
COPY requirments.txt .

# install python libraries
RUN pip install --no-cache-dir -r requirments.txt

# copy code
COPY . .

# run code
CMD ["python", "analyze_job.py"]