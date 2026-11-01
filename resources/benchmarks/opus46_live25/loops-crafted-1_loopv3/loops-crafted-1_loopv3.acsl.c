#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
int SIZE = 50000001;
int main() {
  int i,j;
  i = 0; j=0;
  /*@
    loop invariant 0 <= i;
    loop invariant i % 4 == 0;
    loop assigns i;
    loop variant SIZE - i;
  */
  while(i<SIZE){ 
    if(unknown())	  
      i = i + 8; 
    else
     i = i + 4;    
  }
  j = i/4 ;
    //@ assert( (j * 4) == i);
  return 0;
}
