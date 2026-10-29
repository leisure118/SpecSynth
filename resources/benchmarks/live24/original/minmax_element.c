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
struct size_type_pair {
  size_type first;
  size_type second;
};
typedef struct size_type_pair size_type_pair;
/*@
    assigns         \nothing;
    ensures result: \result.first  == first;
    ensures result: \result.second == second;
*/
static inline
size_type_pair
make_pair(size_type first, size_type second)
{
  size_type_pair pair;
  pair.first  = first;
  pair.second = second;
  return pair;
}
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
  axiomatic ArrayExtrema
  {
    predicate
    MaxElement{L}(value_type* a, integer n, integer max) =
      0 <= max < n && UpperBound(a, n, a[max]);
    predicate
    MinElement{L}(value_type* a, integer n, integer min) =
      0 <= min < n && LowerBound(a, n, a[min]);
  }
*/
/*@
  requires valid:    \valid_read(a + (0..n-1));
  assigns            \nothing;
  ensures result:    0 <= \result.first  <= n;
  ensures result:    0 <= \result.second <= n;
  behavior empty:
    assumes          0 == n;
    assigns          \nothing;
    ensures result:  \result.first == 0;
    ensures result:  \result.second == 0;
  behavior not_empty:
    assumes          0 < n;
    assigns          \nothing;
    ensures result:  0 <= \result.first < n;
    ensures result:  0 <= \result.second < n;
    ensures min:     MinElement(a, n, \result.first);
    ensures first:   StrictLowerBound(a, \result.first, a[\result.first]);
    ensures max:     MaxElement(a, n, \result.second);
    ensures last:    StrictUpperBound(a, \result.second+1, n, a[\result.second]);
*/
size_type_pair
minmax_element(const value_type* a, size_type n)
{
  if (0u < n) {
    size_type min = 0u;
    size_type max = 0u;
    for (size_type i = 0u; i < n; i++) {
      if (a[i] >= a[max]) {
        max = i;
      }
      if (a[i] < a[min]) {
        min = i;
      }
    }
    //@ assert MinElement(a, n, min) && MaxElement(a, n, max);
    return make_pair(min, max);
  }
  return make_pair(n, n);
}