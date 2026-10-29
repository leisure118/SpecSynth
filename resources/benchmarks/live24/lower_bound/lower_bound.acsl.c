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
  axiomatic WeaklyIncreasing
  {
    predicate
    WeaklyIncreasing{L}(value_type* a, integer m, integer n) =
      \forall integer i; m <= i < n-1  ==>  a[i] <= a[i+1];
    predicate
    WeaklyIncreasing{L}(value_type* a, integer n) = WeaklyIncreasing{L}(a, 0, n);
  }
*/
/*@
  axiomatic Increasing
  {
    predicate
    Increasing{L}(value_type* a, integer m, integer n) =
      \forall integer i, j; m <= i < j < n  ==>  a[i] <= a[j];
    predicate
    Increasing{L}(value_type* a, integer n) = Increasing{L}(a, 0, n);
  }
*/
/*@
  axiomatic ArrayBounds
  {
    predicate
    LowerBound{L}(value_type* a, integer m, integer n, value_type v) =
      \forall integer i; m <= i < n  ==>  v <= a[i];
    predicate
    LowerBound{L}(value_type* a, integer n, value_type v) =
      LowerBound{L}(a, 0, n, v);
    predicate
    StrictLowerBound{L}(value_type* a, integer m, integer n, value_type v) =
      \forall integer i; m <= i < n  ==>  v < a[i];
    predicate
    StrictLowerBound{L}(value_type* a, integer n, value_type v) =
      StrictLowerBound{L}(a, 0, n, v);
    predicate
    UpperBound{L}(value_type* a, integer m, integer n, value_type v) =
      \forall integer i; m <= i < n  ==>  a[i] <= v;
    predicate
    UpperBound{L}(value_type* a, integer n, value_type v) =
      UpperBound{L}(a, 0, n, v);
    predicate
    StrictUpperBound{L}(value_type* a, integer m, integer n, value_type v) =
      \forall integer i; m <= i < n  ==>  a[i] < v;
    predicate
    StrictUpperBound{L}(value_type* a, integer n, value_type v) =
      StrictUpperBound{L}(a, 0, n, v);
  }
*/
/*@
  requires \valid_read(a + (0 .. n-1));
  requires Increasing(a, n);
  assigns \nothing;
  ensures \result >= 0;
  ensures \result <= n;
*/
size_type
lower_bound(const value_type* a, size_type n, value_type v)
{
  size_type left  = 0u;
  size_type right = n;
  /*@
    loop invariant 0 <= left <= right <= n;
    loop invariant Increasing(a, n);
    loop invariant LowerBound(a, right, n, v);
    loop assigns left, right;
    loop variant right - left;
  */
  while (left < right) {
    const size_type middle = left + (right - left) / 2u;
    if (a[middle] < v) {
      left = middle + 1u;
    }
    else {
      right = middle;
    }
  }
  //@ assert LowerBound(a, left, n, v);
  return left;
}