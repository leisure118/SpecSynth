/* Auto-generated minimal verifiable slice */
/* Target function: main */
/* Mode: stub */

#include <stdint.h>
#include <unistd.h>
#include <string.h>

typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;

#define SPEC_INT_MAX 2147483647
#define SPEC_INT_MIN -2147483648

int main(void);

/* --- Dependency: spec_abs1 (stub) --- */
/* TODO: add ACSL contract here */
long spec_abs1(int a);

/* === Target: main === */
int main(void)
{
   int a = spec_abs1(SPEC_INT_MIN+1);
   //@ assert a == SPEC_INT_MAX;
}
