FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies required by the OpenEnv core and our scripts
RUN pip install --no-cache-dir openenv-core pydantic openai

# Copy the current project files to the container
COPY . .

# Expose the standard port for Hugging Face Spaces
EXPOSE 7860

# Command to run OpenEnv server using our environment class
CMD ["openenv", "serve", "environment:OnCallEnvironment", "--host", "0.0.0.0", "--port", "7860"]
