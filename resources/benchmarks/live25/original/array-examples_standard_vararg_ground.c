#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#define N 100000
int main( ){
  int aa [N]; 
  int a = 0;
	for(int i = 0; i < N; i++)
	{
	  aa[i] = unknown();
	}
  while( aa[a] >= 0 ) {
    a++;
  }
  int x;
  for ( x = 0 ; x < a ; x++ ) {
    //@ assert(aa[x] >= 0  );
  }
  return 0;
}
