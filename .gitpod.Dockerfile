FROM gitpod/workspace-python-3.11

# Install system dependencies for Pillow (image processing)
USER root
RUN apt-get update && apt-get install -y \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Switch back to gitpod user
USER gitpod

# Pre-install Python dependencies for faster startup
COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

# Create necessary directories
RUN mkdir -p /workspace/uploads /workspace/results /workspace/templates 