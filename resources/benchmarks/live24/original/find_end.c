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
  axiomatic HasSubRange
  {
    predicate
    HasSubRange{L}(value_type* a, integer m, integer n, value_type* b, integer p) =
      \exists integer k; (m <= k <= n-p) && Equal{L,L}(a+k, p, b);
    predicate
    HasSubRange{L}(value_type* a, integer n, value_type* b, integer p) =
      HasSubRange{L}(a, 0, n, b, p);
    lemma HasSubRange_Sizes:
      \forall value_type *a, *b, integer m, n, p;
        HasSubRange(a, m, n, b, p)  ==>  p <= n-m;
  }
*/
/*@
  requires valid:  \valid_read(a + (0..n-1));
  requires valid:  \valid_read(b + (0..n-1));
  assigns          \nothing;
  ensures result:  \result <==> Equal{Here,Here}(a, n, b);
*/
bool
equal(const value_type* a, size_type n, const value_type* b);
size_type
find_end(const value_type* a, size_type n,
         const value_type* b, size_type p)
{
  size_type r = n;
  if ((0u < p) && (p <= n)) {
    for (size_type i = 0u; i <= n - p; ++i) {
      if (equal(a + i, p, b)) {
        r = i;
      }
    }
  }
  //@ assert !HasSubRange(a, r + 1, n, b, p);
  return r;
}