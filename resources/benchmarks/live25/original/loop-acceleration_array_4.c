#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#define N 1024
int main(void) {
  int A[N];
  int i;
  for (i = 0; i < N-1; i++) {
    A[i] = unknown();
  }
  A[N-1] = 0;
  for (i = 0; A[i] != 0; i++) {
  }
  //@ assert(i <= N);
}
