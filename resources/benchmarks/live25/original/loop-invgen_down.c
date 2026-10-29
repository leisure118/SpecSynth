#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include "assert.h"
int main() {
  int n;
  int k = 0;
  int i = 0;
  n = unknown();
  while( i < n ) {
      i++;
      k++;
  }
  int j = n;
  while( j > 0 ) {
      //@ assert(k > 0);
      j--;
      k--;
  }
  return 0;
}
