# Use Ubuntu 24.04 as base with WineHQ repository
FROM docker.io/ubuntu:24.04

# ----------------------------------------------------------------------------------------------
LABEL org.opencontainers.image.source=https://github.com/nodalytics/metatrader-terminal
LABEL org.opencontainers.image.description="MetaTrader 5 Terminal (with API)"
# ----------------------------------------------------------------------------------------------

# Environment Configurations
ENV HOME=/root \
    DISPLAY=:0 \
    SERVER_HOST=0.0.0.0 \
    SERVER_PORT=18812 \
    VNC_DESKTOP_NAME="MetaTrader 5" \
    VNC_GEOMETRY=1280x800 \
    WINEPREFIX=/root/mt \
    STOPSIGNAL=SIGRTMIN+3 \
    XDG_RUNTIME_DIR=/run/user/0 \
    WINEDEBUG=-all

# MT5 Account Details (Provide at runtime)
ENV MT5_PATH="${WINEPREFIX}/drive_c/mt5/terminal64.exe" \
    MT_ACCOUNT_NUMBER=0 \
    MT5_SERVER=''

# Install system dependencies, WineHQ and clean up in a single layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    openbox \
    tigervnc-standalone-server \
    tigervnc-tools \
    supervisor \
    gosu \
    lxterminal \
    nano \
    openssh-client \
    rsync \
    xdg-utils \
    htop \
    tar \
    xzip \
    gzip \
    bzip2 \
    zip \
    unzip \
    wget \
    xvfb \
    libnss3 \
#    nginx-light \
    apache2-utils \
    dbus-x11 \
#   winbind \
    && mkdir -p /usr/share/desktop-directories \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy configuration files
COPY assets/menu.xml /etc/xdg/openbox/
COPY assets/supervisord.conf /etc/

WORKDIR ${HOME}
# Install uv package manager && chmod +x ~/*.exe
ADD https://releases.astral.sh/github/uv/releases/download/0.11.2/uv-x86_64-pc-windows-msvc.zip ./
RUN unzip ./uv-x86_64-pc-windows-msvc.zip -d ./ \
     && rm ./uv-x86_64-pc-windows-msvc.zip

# get MetaTrader and WebView2
ADD https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe ./
ADD https://msedge.sf.dl.delivery.mp.microsoft.com/filestreamingservice/files/f2910a1e-e5a6-4f17-b52d-7faf525d17f8/MicrosoftEdgeWebview2Setup.exe ./

# Copy assets, api and install Python dependencies
COPY assets .
#COPY api/app /root/app/
COPY api/pyproject.toml ./

RUN  mkdir -p ${HOME}/Desktop && \
    cp metatrader.desktop ${HOME}/Desktop/ && \
    cp metatrader.desktop /usr/share/applications/ && \
    chmod +x *.sh

RUN mkdir -p $XDG_RUNTIME_DIR && \
    ~/wine-inst.sh

EXPOSE 5900 8000

CMD ["/root/entrypoint.sh"]