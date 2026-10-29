#include <assert.h>
#define SZ 2048
int main(void) {
  int A[SZ] = {0};
  int B[SZ] = {0};
  int i;
  int tmp;
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
