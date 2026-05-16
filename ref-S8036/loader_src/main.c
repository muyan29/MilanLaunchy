#include <stdalign.h>
#include <stdint.h>

#define CACHE_LINE_SIZE 32

void flush_cache_range(uint32_t start, uint32_t end) {
    uint32_t addr;
    start = start & ~(CACHE_LINE_SIZE - 1);

    for (addr = start; addr < end; addr += CACHE_LINE_SIZE) {
        __asm__ volatile (
            "mcr p15, 0, %0, c7, c10, 1" 
            : 
            : "r" (addr) 
            : "memory"
        );
    }

    __asm__ volatile ("dsb sy" ::: "memory");

    for (addr = start; addr < end; addr += CACHE_LINE_SIZE) {
        __asm__ volatile (
            "mcr p15, 0, %0, c7, c5, 1" 
            : 
            : "r" (addr) 
            : "memory"
        );
    }

    __asm__ volatile ("dsb sy" ::: "memory");
    __asm__ volatile ("isb sy" ::: "memory");
}


int main () {

    volatile uint32_t *src = (volatile uint32_t *)0x21000;
    volatile uint32_t *dst = (volatile uint32_t *)0x0;
    
    uint32_t total_words = 0x18000 / 4;
    uint32_t start_index = 0x10 / 4; 
    for (uint32_t i = start_index; i < total_words; i++) {
        dst[i] = src[i];
    }

    flush_cache_range(0x0, 0x18000);

    __asm__ volatile("dsb" ::: "memory");
    __asm__ volatile("isb" ::: "memory");

    __asm__ volatile (
        "mov pc, %0"     
        : 
        : "r" (0x100)   
        : "memory"
    );
    
    while(1);

    return 0;
}



