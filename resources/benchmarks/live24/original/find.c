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
size_type
find(const value_type* a, size_type n, value_type v)
{
  for (size_type i = 0u; i < n; i++) {
    if (a[i] == v) {
      //@ assert \exists integer k; 0 <= k < n && a[k] == v;
      return i;
    }
  }
  //@ assert \forall integer k; 0 <= k < n ==> a[k] != v;
  return n;
}