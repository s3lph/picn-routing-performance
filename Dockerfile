FROM base/archlinux

RUN pacman -Syu --noconfirm
RUN pacman -S --noconfirm python python-pip git
COPY . .
RUN ./setup.sh

CMD ./run.sh
