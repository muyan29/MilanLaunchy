
SECTIONS
{
  . = 0x20000;
  .text ALIGN(0x10): { *(.text) }
  .data ALIGN(0x20) : { *(.data) }
}
