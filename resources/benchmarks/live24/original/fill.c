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
  axiomatic AllSomeNot
  {
    predicate
    AllEqual(value_type* a, integer m, integer n, value_type v) =
      \forall integer i; m <= i < n  ==>  a[i] == v;
    predicate
    AllEqual(value_type* a, integer m, integer n) =
      AllEqual(a, m, n, a[m]);
    predicate
    AllEqual(value_type* a, integer n, value_type v) =
      AllEqual(a, 0, n, v);
    predicate
    SomeNotEqual{A}(value_type* a, integer m, integer n, value_type v) =
      \exists integer i; m <= i < n && a[i] != v;
    predicate
    SomeNotEqual{A}(value_type* a, integer n, value_type v) =
      SomeNotEqual(a, 0, n, v);
    lemma NotAllEqual_SomeNotEqual:
      \forall value_type *a, v, integer m, n;
        !AllEqual(a, m, n, v)  ==>  SomeNotEqual(a, m, n, v);
    lemma SomeNotEqual_NotAllEqual:
      \forall value_type *a, v, integer m, n;
       SomeNotEqual(a, m, n, v)   ==>  !AllEqual(a, m, n, v);
  }
*/
void
fill(value_type* a, size_type n,  value_type v)
{
  for (size_type i = 0u; i < n; ++i) {
    a[i] = v;
  }
   //@ assert AllEqual(a, n, v);
}