FROM debian:bullseye

WORKDIR /root

RUN apt update
RUN apt install -y  binutils-common \
                    gcc-multilib \
                    vim \
                    gdb-multiarch \
                    git \
                    python \
                    python-pip \
                    bash

RUN pip install --upgrade   pip \
                            ropgadget \
                            pwntools

RUN git clone https://github.com/longld/peda.git ~/peda
RUN echo "source ~/peda/peda.py" >> ~/.gdbinit

COPY rop.c rop.c

RUN gcc rop.c -fno-stack-protector -no-pie -m32 -o rop
