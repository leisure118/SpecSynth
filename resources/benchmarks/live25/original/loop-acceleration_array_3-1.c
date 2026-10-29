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
  for (i = 0; i < N; i++) {
    A[i] = unknown();
  }
  for (i = 0; A[i] != 0; i++) {
    if (i >= N-1) {
      break;
    }
  }
  //@ assert(i <= N);
}
