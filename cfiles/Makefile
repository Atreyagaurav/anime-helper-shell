CC = gcc
CFLAGS = -Wall
LIBS = -lmpv
PLUGFLAGS = -shared -fPIC
OBJ = readstatus.o
CONFIG = --cflags mpv --libs libnotify

all: mpvstatus plugin

%.o: %.c $(DEPS)
	$(CC) $(CFLAGS) $(LIBS) -c -o $@ $<

mpvstatus: $(OBJ)
	gcc $(CFLAGS) -o $@ $^

clean:
	-rm *.o *.so mpvstatus

plugin: plugin.c
	$(CC) -o $@.so $< `pkg-config $(CONFIG)` $(PLUGFLAGS)

install:
	-sudo cp mpvstatus /usr/local/bin/
	-cp plugin.so ~/.config/mpv/scripts

uninstall:
	-sudo rm /usr/local/bin/mpvstatus
	-rm ~/.config/mpv/scripts/plugin.so
