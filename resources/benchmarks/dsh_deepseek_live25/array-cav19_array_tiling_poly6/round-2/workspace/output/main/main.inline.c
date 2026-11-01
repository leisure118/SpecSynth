/* Auto-generated minimal verifiable slice */
/* Target function: main */
/* Mode: inline */

#include <stdint.h>
#include <unistd.h>
#include <string.h>

typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;


extern int unknown();

int main();

/* === Target: main === */
int main()
{
  int S=unknown();
  //@ assert(S>1);
  long long i;
  long long a[S];
  for(i=0;i<S;i++)
    a[i]=((i-1)*(i+1));
  for(i=0;i<S;i++)
    a[i]=a[i]-(i*i);
  for(i=0;i<S;i++){
    //@ assert(a[i]==-1);
  }
  return 0;
}
