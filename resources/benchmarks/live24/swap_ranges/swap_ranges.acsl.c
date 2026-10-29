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
requires \valid(a) && \valid(b);
assigns *a, *b;
ensures *a == \old(*b) && *b == \old(*a);
*/
void swap(int* a, int* b);
/*@
  requires \valid(a+(0 .. n-1));
  requires \valid(b+(0 .. n-1));
  requires \separated(a+(0 .. n-1), b+(0 .. n-1));
  assigns a[0 .. n-1], b[0 .. n-1];
  ensures \forall integer i; 0 <= i < n ==> a[i] == \old(b[i]);
  ensures \forall integer i; 0 <= i < n ==> b[i] == \old(a[i]);
*/
void
swap_ranges(value_type* a, size_type n, value_type* b)
{
  /*@
    loop invariant 0 <= i <= n;
    loop invariant \forall integer j; 0 <= j < i ==> a[j] == \at(b[j],Pre);
    loop invariant \forall integer j; 0 <= j < i ==> b[j] == \at(a[j],Pre);
    loop invariant \forall integer j; i <= j < n ==> a[j] == \at(a[j],Pre);
    loop invariant \forall integer j; i <= j < n ==> b[j] == \at(b[j],Pre);
    loop assigns i, a[0 .. n-1], b[0 .. n-1];
    loop variant n - i;
  */
  for (size_type i = 0u; i < n; ++i) {
    swap(a + i, b + i);
  }
}
int main(){
  value_type a[] = {1, 2, 3, 4, 5};
  value_type b[] = {6, 7, 8, 9, 10};
  int n = 5;
  swap_ranges(a, n, b);
  //@ assert a[0] == 6 && b[0] == 1;
  //@ assert a[1] == 7 && b[1] == 2;
  //@ assert a[2] == 8 && b[2] == 3;
  //@ assert a[3] == 9 && b[3] == 4;
  //@ assert a[4] == 10 && b[4] == 5;
}
