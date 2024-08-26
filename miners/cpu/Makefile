CC = g++

CFLAGS = -lm -Ofast -Wno-deprecated-declarations
TARGET = cpu-sha256

$(TARGET): cpu_sha256.c
	$(CC) cpu_sha256.c $(CFLAGS) -o $(TARGET) -msse4.1 -msha

clean:
	$(RM) $(TARGET)
