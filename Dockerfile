FROM pritunl/archlinux:2018-06-02

RUN pacman -S --noconfirm python python-pip git bc
RUN pip install matplotlib
COPY . .
RUN ./setup.sh

CMD ./run.sh
