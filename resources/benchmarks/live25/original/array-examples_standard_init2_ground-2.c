#include <assert.h>
#define N 100000
int main ( ) {
  int a[N];
  int i = 0;
  while ( i < N ) {
    a[i] = 42;
    i = i + 1;
  }
  i = 0;
  while ( i < N ) {
    a[i] = 43;
    i = i + 1;
  }
  int x;
  for ( x = 0 ; x < N ; x++ ) {
    //@ assert(a[x] == 43  );
  }
  return 0;
}
