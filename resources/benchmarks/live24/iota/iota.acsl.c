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
  axiomatic IotaGenerate
  {
    predicate
    IotaGenerate(value_type* a, integer n, value_type v) =
      \forall integer i; 0 <= i < n  ==>  a[i] == v+i;
  }
*/
/*@
  requires \valid(a + (0 .. n-1));
  assigns a[0 .. n-1];
  ensures \forall integer j; 0 <= j < n ==> a[j] == \old(v) + j;
*/
void
iota(value_type* a, size_type n, value_type v)
{
  /*@
    loop invariant 0 <= i <= n;
    loop invariant \forall integer j; 0 <= j < i ==> a[j] == v - i + j;
    loop invariant v - i == \at(v, Pre);
    loop assigns i, a[0 .. n-1], v;
    loop variant n - i;
  */
  for (size_type i = 0u; i < n; ++i) {
    a[i] = v++;
  }
}
int main(){
    value_type a[10];
    iota(a, 10, 1);
    //@ assert \forall integer i; 0 <= i < 10 ==> a[i] == i + 1;
    return 0;
}