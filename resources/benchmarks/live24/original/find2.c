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
  axiomatic SomeNone
  {
    predicate
    SomeEqual{A}(value_type* a, integer m, integer n, value_type v) =
      \exists integer i; m <= i < n && a[i] == v;
    predicate
    SomeEqual{A}(value_type* a, integer n, value_type v) =
      SomeEqual(a, 0, n, v);
    predicate
    NoneEqual(value_type* a, integer m, integer n, value_type v) =
      \forall integer i; m <= i < n  ==>  a[i] != v;
    predicate
    NoneEqual(value_type* a, integer n, value_type v) =
      NoneEqual(a, 0, n, v);
    lemma NotSomeEqual_NoneEqual:
      \forall value_type *a, v, integer m, n;
        !SomeEqual(a, m, n, v)  ==>  NoneEqual(a, m, n, v);
    lemma NoneEqual_NotSomeEqual:
      \forall value_type *a, v, integer m, n;
       NoneEqual(a, m, n, v)   ==>  !SomeEqual(a, m, n, v);
  }
*/
size_type
find2(const value_type* a, size_type n, value_type v)
{
  for (size_type i = 0u; i < n; i++) {
    if (a[i] == v) {
      //@ assert SomeEqual(a, i+1, v);
      return i;
    }
  }
  //@ assert NoneEqual(a, n, v);
  return n;
}