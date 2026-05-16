NAME := loader


CROSS_COMPILE=arm-none-eabi-
CFLAGS=-Os -I../ -std=gnu99 -fomit-frame-pointer -nostartfiles -ffreestanding -Wextra -Werror -mno-unaligned-access -marm -march=armv7-a

all : $(NAME).elf $(NAME).raw

clean:
	bash -c "rm -f *.o $(NAME).{elf,raw}"

%.o: %.S
	$(CROSS_COMPILE)gcc $(CFLAGS) -c -o $@ $^

%.o: %.c
	$(CROSS_COMPILE)gcc $(CFLAGS) -c -o $@ $^

$(NAME).elf : linker.ld _start.o main.o
	$(CROSS_COMPILE)ld -T $^ -o $@

$(NAME).raw: $(NAME).elf
	$(CROSS_COMPILE)objcopy -O binary $^ $@
