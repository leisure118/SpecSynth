#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include "assert.h"
int main( int argc, char *argv[]){
  int n,l,r,i,j;
  n = unknown();
  if (!(1 <= n && n <= INT_MAX)) return 0;
  l = n/2 + 1;
  r = n;
  if(l>1) {
    l--;
  } else {
    r--;
  }
  while(r > 1) {
    i = l;
    j = 2*l;
    while(j <= r) {
      if( j < r) {
	//@ assert(1 <= j);
	//@ assert(j <= n);
	//@ assert(1 <= j+1);
	//@ assert(j+1 <= n);
	if( unknown() )
	  j = j + 1;
      }
      //@ assert(1 <= j);
      //@ assert(j <= n);
      if( unknown() ) { 
      	break;
      }
      //@ assert(1 <= i);
      //@ assert(i <= n);
      //@ assert(1 <= j);
      //@ assert(j <= n);
      i = j;
      j = 2*j;
    }
    if(l > 1) {
      //@ assert(1 <= l);
      //@ assert(l <= n);
      l--;
    } else {
      //@ assert(1 <= r);
      //@ assert(r <= n);
      r--;
    }
  }
  return 0;
}
