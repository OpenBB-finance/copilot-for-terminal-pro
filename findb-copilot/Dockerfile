FROM python:3.11.6-slim-bullseye
# --platform=linux/amd64 

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    PYSETUP_PATH="/opt/pysetup"

# Include the virtual environment binaries in PATH
ENV PATH="$VENV_PATH/bin:$PATH"

# Install dependencies required for building some Python packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR $PYSETUP_PATH

# Install poetry
RUN pip install poetry==1.7.1

# Copy lock and pyproject files
COPY poetry.lock pyproject.toml ./

# Install dependencies
RUN poetry config installer.max-workers 10 \
    && poetry config virtualenvs.create false \
    && poetry install --without dev --no-interaction --no-ansi --no-cache --no-root

# Set working directory for the application
WORKDIR /opt/app

# Copy application files
COPY findb_copilot ./findb_copilot
COPY start.sh ./start.sh

# Expose the port the app runs on
EXPOSE 7779

# Command to run the application
ENTRYPOINT ["bash", "start.sh"]
