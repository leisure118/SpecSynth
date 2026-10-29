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
  axiomatic Unchanged
  {
    predicate
    Unchanged{K,L}(value_type* a, integer m, integer n) =
      \forall integer i; m <= i < n ==>  \at(a[i],K) == \at(a[i],L);
    predicate
    Unchanged{K,L}(value_type* a, integer n) = Unchanged{K,L}(a, 0, n);
  }
*/
/*@
  axiomatic Reverse
  {
    predicate
    Reverse{K,L}(value_type* a, integer n, value_type* b) =
      \forall integer i; 0 <= i < n  ==>  \at(a[i],K) == \at(b[n-1-i], L);
    predicate
    Reverse{K,L}(value_type* a, integer m, integer n,
                 value_type* b, integer p) = Reverse{K,L}(a+m, n-m, b+p);
    predicate
    Reverse{K,L}(value_type* a, integer m, integer n, value_type* b) =
      Reverse{K,L}(a, m, n, b, m);
    predicate
    Reverse{K,L}(value_type* a, integer m, integer n, integer p) =
      Reverse{K,L}(a, m, n, a, p);
    predicate
    Reverse{K,L}(value_type* a, integer m, integer n) =
      Reverse{K,L}(a, m, n, m);
    predicate
    Reverse{K,L}(value_type* a, integer n) = Reverse{K,L}(a, 0, n);
  }
*/
/*@
  requires valid:  \valid(a + (0..n-1));
  assigns          a[0..n-1];
  ensures reverse: Reverse{Old,Here}(a, n);
*/
void
reverse(value_type* a, size_type n);
/*@
  axiomatic Equal
  {
    predicate
    Equal{K,L}(value_type* a, integer m, integer n, value_type* b) =
      \forall integer i; m <= i < n  ==>  \at(a[i],K) == \at(b[i],L);
    predicate
    Equal{K,L}(value_type* a, integer n, value_type* b) =
      Equal{K,L}(a, 0, n, b);
    predicate
    Equal{K,L}(value_type* a, integer m, integer n,
               value_type* b, integer p) = Equal{K,L}(a+m, n-m, b+p);
    predicate
    Equal{K,L}(value_type* a, integer m, integer n, integer p) =
      Equal{K,L}(a, m, n, a, p);
  }
*/
size_type
rotate(value_type* a, size_type m, size_type n)
{
  if ((0u < m) && (m < n)) {
    reverse(a,  m);
    reverse(a + m, n - m);
    reverse(a, n);
    //@ assert left:   Equal{Pre,Here}(a, 0, m, n-m);
    //@ assert right:  Equal{Pre,Here}(a, m, n, 0);
  }
  return n - m;
}