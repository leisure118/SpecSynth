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
  while(i<n){ 
    i = i + 4;
    j = i +2;    
  }
  k =i;
  while( (j%2) == 0){
   j-=4;
   k -=4; 
  }
  //@ assert( (k%2) == 0 );
  return 0;
}
