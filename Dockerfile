FROM base/archlinux

RUN pacman -Syu --noconfirm
RUN pacman -S --noconfirm python python-pip git bc
RUN pip install matplotlib
COPY . .
RUN ./setup.sh

CMD ./run.sh
