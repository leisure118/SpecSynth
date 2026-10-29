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
  axiomatic HasEqualNeighbors
  {
    predicate
    HasEqualNeighbors{L}(value_type* a, integer n) =
      \exists integer i; 0 <= i < n-1 && a[i] == a[i+1];
  }
*/
/*@
  lemma HasEqualNeighbors_at_match{L}:
    \forall value_type *a, integer i;
      0 <= i && a[i] == a[i+1] ==> HasEqualNeighbors(a, i+2);
*/
size_type
adjacent_find(const value_type* a, size_type n)
{
  if (1u < n) {
    /*@
      loop invariant 0 <= i <= n;
      loop invariant i <= n - 1;
      loop invariant \forall integer j; 0 <= j < i ==> a[j] != a[j+1];
      loop assigns i;
      loop variant n - i;
    */
    for (size_type i = 0u; i + 1u < n; ++i) {
      if (a[i] == a[i + 1u]) {
        //@ assert HasEqualNeighbors(a, i+2);
        return  i;
      }
    }
  }
  //@ assert !HasEqualNeighbors(a, n);
  return n;
}