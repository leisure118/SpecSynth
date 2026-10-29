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
/*@
  axiomatic HasConstantSubRange
  {
    predicate
    HasConstantSubRange{L}(value_type* a, integer m, integer n, value_type v, integer p) =
      \exists integer k; m <= k <= n-p && AllEqual(a, k, k+p, v);
    predicate
    HasConstantSubRange{L}(value_type* a, integer n, value_type v, integer p) =
      HasConstantSubRange(a, 0, n, v, p);
    lemma HasConstantSubRange_Sizes:
      \forall value_type *a, v, integer n, p;
        HasConstantSubRange(a, n, v, p)  ==>  p <= n;
  }
*/
size_type
search_n(const value_type* a, size_type n, value_type v, size_type p)
{
  if (0u < p) {
    if (p <= n) {
      size_type start = 0u;
      for (size_type i = 0u; i < n; ++i) {
        if (a[i] != v) {
          start = i + 1u;
          //@ assert not_found: !HasConstantSubRange(a, i+1, v, p);
        }
        else {
          //@ assert match: a[i] == v;
          //@ assert match: AllEqual(a, start, i+1, v);
          if (p == i + 1u - start) {
            //@ assert bound: start + p == i + 1;
            //@ assert match: AllEqual(a, start, start+p, v);
            //@ assert match: \exists integer k; 0 <= k <= n-p && AllEqual(a, k, k+p, v);
            //@ assert match: HasConstantSubRange(a, n, v, p);
            return start;
          }
          else {
            //@ assert bound: i + 1 < start + p;
            continue;
          }
        }
        //@ assert not_found: !HasConstantSubRange(a, i+1, v, p);
      }
      //@ assert not_found: !HasConstantSubRange(a, n, v, p);
      return n;
    }
    else {
      //@ assert not_found: n < p;
      //@ assert not_found: !HasConstantSubRange(a, n, v, p);
      return n;
    }
  }
  else {
    //@ assert bound: p == 0;
    //@ assert match: AllEqual(a, 0, 0, v);
    //@ assert match: HasConstantSubRange(a, n, v, 0);
    return 0u;
  }
}