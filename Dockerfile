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
RUN dpkg --add-architecture i386 && \
    apt-get update && \
    apt-get install -y wine32 && \
    rm -rf /var/lib/apt/lists/* && \
    wineboot --init && \
    wget -q https://jrsoftware.org/download.php/is.exe -O /tmp/is.exe && \
    xvfb-run wine /tmp/is.exe /VERYSILENT /SUPPRESSMSGBOXES /DIR="C:\\InnoSetup" && \
    rm /tmp/is.exe

# Pre-cache common embeddable Python versions
RUN mkdir -p /snackbox/cache/python && \
    for v in 3.11.12 3.12.10; do \
        wget -q "https://www.python.org/ftp/python/${v}/python-${v}-embed-amd64.zip" \
            -O "/snackbox/cache/python/python-${v}-embed-amd64.zip"; \
    done

# Install snackbox
COPY . /snackbox/src
RUN pip3 install --break-system-packages /snackbox/src

# Environment for cross-compilation
ENV SNACKBOX_CACHE_DIR=/snackbox/cache
ENV SNACKBOX_ISCC_PATH="xvfb-run wine C:\\InnoSetup\\ISCC.exe"
ENV SNACKBOX_GCC=x86_64-w64-mingw32-gcc
ENV SNACKBOX_WINDRES=x86_64-w64-mingw32-windres

WORKDIR /project
ENTRYPOINT ["snackbox"]
CMD ["--help"]
