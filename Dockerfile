FROM base/archlinux

RUN pacman -Syu --noconfirm
RUN pacman -S --noconfirm python python-pip git
COPY setup.sh setup.sh
COPY docker-run.sh docker-run.sh
RUN ./setup.sh

CMD ./docker-run.sh
