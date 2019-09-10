FROM debian:bullseye-slim

WORKDIR /root

RUN apt update && apt install -y --no-install-recommends    binutils-common \
                                                            gcc-multilib \
                                                            vim \
                                                            gdb-multiarch \
                                                            git \
                                                            python \
                                                            python-dev \
                                                            python-pip \
                                                            bash \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade setuptools
RUN pip install --upgrade   pip \
                            ropgadget \
                            pwntools

RUN git clone https://github.com/longld/peda.git ~/.peda
RUN echo "source ~/.peda/peda.py" >> ~/.gdbinit

COPY rop.c rop.c
COPY exploit.py exploit.py

RUN gcc rop.c -fno-stack-protector -no-pie -m32 -o rop
