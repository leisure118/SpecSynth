/* Auto-generated minimal verifiable slice */
/* Target function: per */
/* Mode: stub */

#include <stdint.h>
#include <unistd.h>
#include <string.h>

typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;


unsigned per(const char x[], unsigned l);

/* --- Dependency: has_period (stub) --- */
/* TODO: add ACSL contract here */
unsigned has_period(const char x[], unsigned int p, unsigned l);

/* === Target: per === */
unsigned per(const char x[], unsigned l) {
    unsigned int p;
    for(p = 1; p < l; ++p) {
        if(has_period(x,p,l))
            return p;
    }
    //@ assert is_periodic(x,p,l);
    return p;
}
