#include <limits.h>
#ifndef __cplusplus
typedef int bool;
#define false		((bool)0)
#define true		((bool)1)
#endif
typedef int value_type;
#define VALUE_TYPE_MAX  INT_MAX
#define VALUE_TYPE_MIN  INT_MIN
typedef unsigned int size_type;
#define SIZE_TYPE_MAX  UINT_MAX
/*@
  axiomatic C_Bit
  {
    lemma RandomNumberModulo:
      \forall unsigned long long a;
        (a % (1ull << 48)) < (1ull << 48);
  }
*/
/*@
  requires valid: \valid(seed + (0..2));
  assigns seed[0..2];
  ensures lower:  0 <= \result;
  ensures upper:  \result <= 0x7fffffff;
*/
static long
my_lrand48(unsigned short* seed)
{
  unsigned long long state = (unsigned long long)seed[0] << 32
                             | (unsigned long long)seed[1] << 16
                             | (unsigned long long)seed[2];
  state = (0x5deece66dull * state + 0xbull) % (1ull << 48);
  //@ assert lower: state < (1ull << 48);
  long result = state / (1ull << 17);
  //@ assert lower: 0 <= result;
  seed[0u] = state >> 32 & 0xffff;
  seed[1u] = state >> 16 & 0xffff;
  seed[2u] = state >>  8 & 0xffff;
  return result;
}
size_type
random_number(unsigned short* state, size_type n)
{
  return my_lrand48(state) % n;
}
/*@
  requires  \valid(state + (0..2));
  assigns   state[0..2];
*/
void
random_init(unsigned short* state)
{
  state[0] = 0x243f;
  state[1] = 0x6a88;
  state[2] = 0x85a3;
}