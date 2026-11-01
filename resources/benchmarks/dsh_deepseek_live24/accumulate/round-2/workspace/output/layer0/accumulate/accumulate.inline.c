#ifndef TYPEDEFS_H_INCLUDED
#define TYPEDEFS_H_INCLUDED
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
#endif
#include<limits.h>
/*@
  axiomatic Unchanged
  {
    predicate
    Unchanged{K,L}(value_type* a, integer m, integer n) =
      \forall integer i; m <= i < n ==>  \at(a[i],K) == \at(a[i],L);
    predicate
    Unchanged{K,L}(value_type* a, integer n) = Unchanged{K,L}(a, 0, n);
  }
  axiomatic UnchangedLemmas
  {
    lemma Unchanged_Shrink{K,L}:
      \forall value_type *a, integer m, n, p, q;
         m <= p <= q <= n         ==>
         Unchanged{K,L}(a, m, n)  ==>
         Unchanged{K,L}(a, p, q);
    lemma Unchanged_Extend{K,L}:
      \forall value_type *a, integer n;
        Unchanged{K,L}(a, n)        ==>
        \at(a[n],K) == \at(a[n],L)  ==>
        Unchanged{K,L}(a, n+1);
    lemma Unchanged_Symmetric{K,L}:
      \forall value_type *a, integer m, n;
        Unchanged{K,L}(a, m, n)  ==>
        Unchanged{L,K}(a, m, n);
    lemma Unchanged_Transitive{K,L,M}:
      \forall value_type *a, integer m, n;
        Unchanged{K,L}(a, m, n)  ==>
        Unchanged{L,M}(a, m, n)  ==>
        Unchanged{K,M}(a, m, n);
  }
  axiomatic Accumulate
  {
    logic integer
    Accumulate{L}(value_type* a, integer n, integer init) =
      n <= 0 ? init : Accumulate(a, n-1, init) + a[n-1];
    predicate
    AccumulateBounds{L}(value_type* a, integer n, value_type init) =
      \forall integer i; 0 <= i <= n  ==>
        VALUE_TYPE_MIN <= Accumulate(a, i, init) <= VALUE_TYPE_MAX;
    lemma Accumulate_Init:
      \forall value_type *a, init, integer n;
         n <= 0  ==>  Accumulate(a, n, init) == init;
  }
*/
value_type
accumulate(const value_type* a, size_type n, value_type init)
{
  for (size_type i = 0u; i < n; ++i) {
    //@ assert rte_help: init + a[i] == Accumulate(a, i+1, \at(init,Pre));
    init = init + a[i];
  }
  return init;
}