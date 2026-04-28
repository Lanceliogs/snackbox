FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

# Install base dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    mingw-w64 \
    wine64 \
    wget \
    unzip \
    git \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Initialize Wine and install Inno Setup
ENV WINEDEBUG=-all
ENV DISPLAY=:99

RUN dpkg --add-architecture i386 && \
    apt-get update && \
    apt-get install -y wine32 && \
    rm -rf /var/lib/apt/lists/*

RUN Xvfb :99 -screen 0 1024x768x16 & \
    sleep 2 && \
    wineboot --init && \
    wget -q https://jrsoftware.org/download.php/is.exe -O /tmp/is.exe && \
    wine /tmp/is.exe /VERYSILENT /SUPPRESSMSGBOXES /DIR="C:\\InnoSetup" && \
    rm /tmp/is.exe && \
    wineserver -k || true

# Pre-cache common embeddable Python versions
RUN mkdir -p /snackbox/cache/python && \
    for v in 3.11.12 3.12.10; do \
        wget -q "https://www.python.org/ftp/python/${v}/python-${v}-embed-amd64.zip" \
            -O "/snackbox/cache/python/python-${v}-embed-amd64.zip"; \
    done

# Install Poetry and snackbox
RUN pip3 install --break-system-packages poetry
COPY . /snackbox/src
RUN pip3 install --break-system-packages /snackbox/src

# Environment for cross-compilation
ENV SNACKBOX_CACHE_DIR=/snackbox/cache
ENV SNACKBOX_ISCC_PATH="/root/.wine/drive_c/InnoSetup/ISCC.exe"
ENV SNACKBOX_GCC=x86_64-w64-mingw32-gcc
ENV SNACKBOX_WINDRES=x86_64-w64-mingw32-windres

WORKDIR /project

# Clean up Xvfb lock from build
RUN rm -f /tmp/.X99-lock

# Wrapper script to start Xvfb before running snackbox
RUN printf '#!/bin/bash\nrm -f /tmp/.X99-lock\nXvfb :99 -screen 0 1024x768x16 >/dev/null 2>&1 &\nsleep 1\nexec snackbox "$@"\n' > /usr/local/bin/snackbox-wrapper && \
    chmod +x /usr/local/bin/snackbox-wrapper

ENTRYPOINT ["snackbox-wrapper"]
CMD ["--help"]
