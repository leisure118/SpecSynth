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
*/
/*@
  inductive CountInd{L}(value_type *a, integer n, value_type v, integer sum)
  {
    case Nil{L}:
      \forall value_type *a, v, integer n;
        n <= 0  ==>  CountInd{L}(a, n, v, 0);
    case Hit{L}:
      \forall value_type *a, v, integer n, sum;
        0 < n  &&  a[n-1] == v  &&  CountInd{L}(a, n-1, v, sum)  ==>
        CountInd{L}(a, n, v, sum + 1);
    case Miss{L}:
      \forall value_type *a, v, integer n, sum;
        0 < n  &&  a[n-1] != v  &&  CountInd{L}(a, n-1, v, sum)  ==>
        CountInd{L}(a, n, v, sum);
  }
*/
/*@
  axiomatic CountIndImplicit
  {
    lemma CountInd_Empty{L}:
      \forall value_type *a, v, integer n;
       n <= 0  ==>  CountInd(a, n, v, 0);
    lemma CountInd_Hit{L}:
      \forall value_type *a, v, integer n, sum;
        0 < n                     ==>
        a[n-1] == v               ==>
        CountInd(a, n-1, v, sum)  ==>
        CountInd(a,   n, v, sum+1);
    lemma CountInd_Miss{L}:
      \forall value_type *a, v, integer n, sum;
        0 < n                     ==>
        a[n-1] != v               ==>
        CountInd(a, n-1, v, sum)  ==>
        CountInd(a,   n, v, sum);
  }
*/
/*@
  axiomatic Count
  {
    logic integer
    Count(value_type* a, integer m, integer n, value_type v) =
      n <= m ? 0 : Count(a, m, n-1, v) + (a[n-1] == v ? 1 : 0);
    logic integer
    Count(value_type* a, integer n, value_type v) = Count(a, 0, n, v);
    lemma Count_Empty:
      \forall value_type *a, v, integer m, n;
        n <= m  ==>  Count(a, m, n, v) == 0;
    lemma Count_Hit:
      \forall value_type *a, v, integer n, m;
        m < n        ==>
        a[n-1] == v  ==>
        Count(a, m, n, v) == Count(a, m, n-1, v) + 1;
    lemma Count_Miss:
      \forall value_type *a, v, integer n, m;
        m < n        ==>
        a[n-1] != v  ==>
        Count(a, m, n, v) == Count(a, m, n-1, v);
    lemma Count_One:
      \forall value_type *a, v, integer m, n;
        m <= n  ==>  Count(a, m, n+1, v) == Count(a, m, n, v) + Count(a, n, n+1, v);
    lemma Count_Single{K,L}:
      \forall value_type *a, *b, v, integer m, n;
        \at(a[m],K) == \at(b[n],L)  ==>
        Count{K}(a, m, m+1, v) == Count{L}(b, n, n+1, v);
    lemma Count_Single_Bounds:
      \forall value_type *a, v, integer n;
        0 <= Count(a, n, n+1, v) <= 1;
    lemma Count_Single_Shift:
      \forall value_type *a, v, integer n;
        0 <= n  ==>  Count(a+n, 0, 1, v) == Count(a, n, n+1, v);
  }
*/
/*@
  axiomatic CountIndLemmas
  {
    lemma CountInd_Inverse:
      \forall value_type *a, v, integer n, sum;
        CountInd(a, n, v, sum)  ==>
          (n <= 0 && sum == 0) ||
          (0 < n && a[n-1] != v && CountInd(a, n-1, v, sum)) ||
          (0 < n && a[n-1] == v && CountInd(a, n-1, v, sum-1));
  }
*/
size_type
count2(const value_type* a, size_type n, value_type v)
{
  size_type counted = 0u;
  for (size_type i = 0u; i < n; ++i) {
    if (a[i] == v) {
      counted++;
      //@ assert count: CountInd(a, i+1, v, counted);
    }
  }
  return counted;
}