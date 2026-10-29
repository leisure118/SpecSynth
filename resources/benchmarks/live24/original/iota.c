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
void
iota(value_type* a, size_type n, value_type v)
{
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