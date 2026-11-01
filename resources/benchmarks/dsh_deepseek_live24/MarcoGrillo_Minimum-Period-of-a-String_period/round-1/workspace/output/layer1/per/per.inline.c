/* Auto-generated minimal verifiable slice */
/* Target function: per */
/* Mode: inline */

#include <stdint.h>
#include <unistd.h>
#include <string.h>

typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;


unsigned has_period(const char x[], unsigned int p, unsigned l);
unsigned per(const char x[], unsigned l);

unsigned has_period(const char x[], unsigned int p, unsigned l) {
    if (p == l) return 1;
    if ((l % p) != 0) return 0;
        /*@
            loop assigns i;
            loop invariant \forall unsigned int j; 0 <= j < i ==> (x[j] == x[j+p]);
            loop invariant i <= l-p-1;
            loop invariant i >= 0;
        */
        for (unsigned i = 0 ; i < l-p-1 ; ++i) {
            if (x[i] != x[i + p])
                return 0;
        }     
    return 1; 
}

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
