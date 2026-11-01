#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#define SZ 2048
int main(void) {
  int A[SZ];
  int B[SZ];
  int i;
  int tmp;
  /*@
    loop invariant 0 <= i <= SZ;
    loop assigns i, A[0 .. SZ-1], B[0 .. SZ-1];
    loop variant SZ - i;
  */
  for (i = 0; i < SZ; i++) {
    A[i] = unknown();
    B[i] = unknown();
  }
  /*@
    loop invariant 0 <= i <= SZ;
    loop invariant \forall integer j; 0 <= j < i ==> B[j] == A[j];
    loop assigns i, tmp, B[0 .. SZ-1];
    loop variant SZ - i;
  */
  for (i = 0; i < SZ; i++) {
    tmp = A[i];
    B[i] = tmp;
  }
  //@ assert(A[SZ/2] == B[SZ/2]);
}
