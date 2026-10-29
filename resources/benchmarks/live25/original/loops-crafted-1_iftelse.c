#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
int SIZE = 20000001;
int main() {
  int n,i,k,j;
  n = unknown();
  if (!(n <= SIZE)) return 0;
  i = j = k = 0;
  while( i < n ) {
    i = i + 3;
    if(i%2)
	    j = j+3;
    else
	    k = k+3;
    if(n>0){
      //@assert( (i/2<=j) );
  }
  return 0;
  }
}
