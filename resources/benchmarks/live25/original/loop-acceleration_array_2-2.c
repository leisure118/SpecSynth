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
  for (i = 0; i < SZ; i++) {
    A[i] = unknown();
    B[i] = unknown();
  }
  for (i = 0; i < SZ; i++) {
    tmp = A[i];
    B[i] = tmp;
  }
  //@ assert(A[SZ/2] == B[SZ/2]);
}
