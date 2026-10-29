#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include "assert.h"
int main() {
  int n;
  int i = 0;
  int k = 0;
  n = unknown();
  while( i < n ) {
	i++;
	k++;
  }
  int j = 0;
  while( j < n ) {
    //@ assert(k > 0);
    j++;
    k--;
  }
}
