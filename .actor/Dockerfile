FROM apify/actor-python:3.12

# Second, copy just requirements.txt into the Actor image,
# since it should be the only file that affects the dependency install in the next step,
# in order to speed up the build
COPY pyproject.toml uv.lock ./

# Update and install curl
RUN apt-get update && apt-get install -y curl

# Install Node.js 22.x LTS and npm
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    npm install -g mcp-remote && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install the packages specified in requirements.txt,
# Print the installed Python version, pip version
# and all installed packages with their versions for debugging
RUN echo "Python version:" \
    && python --version \
    && echo "Pip version:" \
    && pip --version \
    && echo "Node.js version:" \
    && node --version \
    && echo "npm version:" \
    && npm --version \
    && echo "Installing uv:" \
    && pip install --no-cache-dir uv \
    && echo "Installing dependencies:" \
    && uv sync --frozen --no-dev \
    && echo "All installed Python packages:" \
    && uv pip freeze

# Next, copy the remaining files and directories with the source code.
# Since we do this after installing the dependencies, quick build will be really fast
# for most source file changes.
COPY . ./

# Specify how to launch the source code of your Actor.
# By default, the "python3 -m ." command is run
ENV PATH="/usr/src/app/.venv/bin:$PATH"
CMD ["python3", "-m", "src"]
