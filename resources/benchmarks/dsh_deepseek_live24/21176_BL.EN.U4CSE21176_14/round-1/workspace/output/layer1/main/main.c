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


int main();

/* --- Dependency: check (stub) --- */
/* TODO: add ACSL contract here */
int check(int val);

/* === Target: main === */
int main(){
int x=4;
int r=check(x);
//@assert x==4;
}
