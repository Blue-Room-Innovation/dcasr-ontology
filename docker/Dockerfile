FROM node:20-bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV WORKSPACE_ROOT=/workspace
RUN apt-get update && apt-get install -y --no-install-recommends \
  openjdk-17-jre-headless \
  python3 \
  python3-pip \
  python3-venv \
  curl \
  ca-certificates \
  graphviz \
  && rm -rf /var/lib/apt/lists/*

# Create venv and install Python dependencies
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

# Install ROBOT
RUN mkdir -p /opt/robot \
  && curl -fsSL -o /opt/robot/robot.jar https://github.com/ontodev/robot/releases/latest/download/robot.jar \
  && printf '#!/bin/sh\nexec java -jar /opt/robot/robot.jar "$@"\n' > /usr/local/bin/robot \
  && chmod +x /usr/local/bin/robot

WORKDIR /workspace

# Copy package files and install npm dependencies
COPY package*.json ./
RUN npm ci --quiet

# Copy Python requirements and install
COPY scripts/requirements.txt ./scripts/
RUN . /opt/venv/bin/activate && pip install --no-cache-dir -r scripts/requirements.txt

# Copy all project files
COPY . .

# Create wrapper script to activate venv before running commands
RUN echo '#!/bin/bash\n. /opt/venv/bin/activate\nexec "$@"' > /usr/local/bin/run-with-venv \
  && chmod +x /usr/local/bin/run-with-venv

ENTRYPOINT ["/usr/local/bin/run-with-venv"]
CMD ["bash"]
