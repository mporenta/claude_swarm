FROM node:20

ARG TZ
ENV TZ="$TZ"

ARG CLAUDE_CODE_VERSION=latest
ARG GIT_DELTA_VERSION=0.18.2
ARG USERNAME=node

# Base packages incl. Python 3.11 and venv support
RUN apt-get update && apt-get install -y --no-install-recommends \
  ca-certificates curl build-essential less git procps sudo fzf zsh man-db unzip gnupg2 \
  iptables ipset iproute2 dnsutils aggregate jq nano vim \
  python3.11 python3.11-dev python3.11-venv python3-pip python3-setuptools python3-wheel python3-dev \
  && rm -rf /var/lib/apt/lists/*

# Optional: make python/python3 point to 3.11 (not strictly needed once venv is used)
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

# Create and prime a global venv for the image
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN python3.11 -m venv "$VIRTUAL_ENV" && \
    "$VIRTUAL_ENV/bin/python" -m pip install --upgrade pip

# Install Python deps into the venv (avoids PEP 668)
COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

# Git delta (no sudo needed in a Docker build)
RUN ARCH="$(dpkg --print-architecture)" && \
    wget -q "https://github.com/dandavison/delta/releases/download/${GIT_DELTA_VERSION}/git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb" && \
    dpkg -i "git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb" && \
    rm "git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb"

# Create workspace and config; persist bash/zsh history
RUN mkdir -p /workspace /home/node/.claude /commandhistory /usr/local/share/npm-global && \
    touch /commandhistory/.bash_history && \
    chown -R ${USERNAME}:${USERNAME} /workspace /home/node/.claude /commandhistory /usr/local/share/npm-global

# Give node permission to run firewall init as root (if you need it later)
COPY init-firewall.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/init-firewall.sh && \
    printf "node ALL=(root) NOPASSWD: /usr/local/bin/init-firewall.sh\n" > /etc/sudoers.d/node-firewall && \
    chmod 0440 /etc/sudoers.d/node-firewall

# Environment for devcontainers / shells
ENV DEVCONTAINER=true
ENV NPM_CONFIG_PREFIX=/usr/local/share/npm-global
ENV PATH="$PATH:/usr/local/share/npm-global/bin"
ENV SHELL=/bin/zsh
ENV EDITOR=nano
ENV VISUAL=nano

WORKDIR /workspace

# Switch to non-root user for global npm installs and shell setup
USER node

# zsh setup
ARG ZSH_IN_DOCKER_VERSION=1.2.0
RUN sh -c "$(wget -O- https://github.com/deluan/zsh-in-docker/releases/download/v${ZSH_IN_DOCKER_VERSION}/zsh-in-docker.sh)" -- \
  -p git \
  -p fzf \
  -a "source /usr/share/doc/fzf/examples/key-bindings.zsh" \
  -a "source /usr/share/doc/fzf/examples/completion.zsh" \
  -a "export PROMPT_COMMAND='history -a' && export HISTFILE=/commandhistory/.bash_history" \
  -x

# Claude Code CLI
RUN npm install -g @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}

# Default back to node user with venv-first PATH
USER node
