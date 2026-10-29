#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
int SIZE = 50000001;
int unknown();
int main() {
  int n,i,j;
  n = unknown();
  if (!(n <= SIZE)) return 0;
  i = 0; j=0;
  while(i<n){ 
    if(unknown())	  
      i = i + 6; 
    else
     i = i + 3;    
  }
  //@ assert( (i%3) == 0 );
  return 0;
}
