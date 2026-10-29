#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
int SIZE = 50000001;
int main() {
  int n,i,j,k;
  n = unknown();
  if (!(n <= SIZE)) return 0;
  i = 0; j=0;
  /*@
    loop invariant 0 <= i;
    loop invariant i % 4 == 0;
    loop invariant j % 2 == 0;
    loop assigns i, j;
    loop variant n - i;
  */
  while(i<n){ 
    i = i + 4;
    j = i +2;    
  }
  k =i;
  /*@
    loop invariant j % 2 == 0;
    loop invariant k % 2 == 0;
    loop assigns j, k;
  */
  while( (j%2) == 0){
   j-=4;
   k -=4; 
  }
  //@ assert( (k%2) == 0 );
  return 0;
}
